"""Testes F4b — frete, pagamento tokenizado, NF-e e e-mails."""

from __future__ import annotations

import hashlib
import hmac
import json

import pytest
from django.core import mail
from django.core.exceptions import ValidationError
from django.urls import reverse

from apps.cart.services import add_to_cart, get_or_create_cart
from apps.catalog.models import Category
from apps.checkout.payments import sanitize_payment_payload
from apps.checkout.services import build_order_from_cart, pay_order, refund_order_payment
from apps.checkout.shipping import calculate_shipping
from apps.checkout.tasks import emit_invoice_task
from apps.notifications.models import EmailLog
from apps.orders.models import Invoice, Order, Payment
from apps.products.models import Product, ProductTranslation, Stock


@pytest.fixture
def product(db):
    cat = Category.objects.create(name="Peças", slug="pecas")
    p = Product.objects.create(
        sku="CHK-001",
        brand="Mondial",
        model_code="X1",
        price="100.00",
        status=Product.Status.PUBLISHED,
        category=cat,
        weight_kg="1.0",
    )
    ProductTranslation.objects.create(product=p, locale="pt-BR", name="Peça checkout")
    Stock.objects.create(product=p, quantity_available=5, quantity_reserved=0)
    return p


@pytest.fixture
def cart_ready(client, product):
    session = client.session
    session.save()
    client.post(reverse("cart:add"), {"product_id": product.pk, "quantity": 1})
    return product


SHIPPING = {
    "shipping_name": "Henrique Teste",
    "shipping_phone": "11999999999",
    "shipping_cep": "01310100",
    "shipping_street": "Av Paulista",
    "shipping_number": "1000",
    "shipping_complement": "",
    "shipping_district": "Bela Vista",
    "shipping_city": "São Paulo",
    "shipping_state": "SP",
}


@pytest.mark.django_db
def test_shipping_fixed_fallback():
    opts = calculate_shipping(cep="01310-100", subtotal=50)
    assert len(opts) >= 1
    assert opts[0].source == "fixed"


@pytest.mark.django_db
def test_shipping_invalid_cep():
    with pytest.raises(ValueError):
        calculate_shipping(cep="123", subtotal=10)


def test_sanitize_strips_pan():
    dirty = {"payment_token": "tok_x", "card_number": "4111111111111111", "cvv": "123"}
    clean = sanitize_payment_payload(dirty)
    assert "card_number" not in clean
    assert "cvv" not in clean
    assert clean["payment_token"] == "tok_x"


@pytest.mark.django_db
def test_checkout_pay_success(rf, product):
    request = rf.get("/")
    from django.contrib.sessions.middleware import SessionMiddleware

    SessionMiddleware(lambda r: None).process_request(request)
    request.session.save()
    from django.contrib.auth.models import AnonymousUser

    request.user = AnonymousUser()
    add_to_cart(request, product, 1)
    cart = get_or_create_cart(request)
    order = build_order_from_cart(
        cart=cart,
        email="cliente@example.com",
        shipping=SHIPPING,
        shipping_option_id="fixed-econ",
        user=request.user,
    )
    payment = pay_order(order=order, payment_token="tok_sandbox_4242")
    order.refresh_from_db()
    product.stock.refresh_from_db()
    assert payment.status == Payment.Status.PAID
    assert order.status == Order.Status.PAID
    assert product.stock.quantity_available == 4
    assert Invoice.objects.filter(order=order, status=Invoice.Status.ISSUED).exists()
    assert EmailLog.objects.filter(
        order=order, kind=EmailLog.Kind.ORDER_CONFIRMATION, status=EmailLog.Status.SENT
    ).exists()
    assert len(mail.outbox) >= 1
    # nenhum PAN no payment
    assert "4111" not in payment.payment_token
    assert payment.last4


@pytest.mark.django_db
def test_checkout_pay_failure(rf, product):
    request = rf.get("/")
    from django.contrib.auth.models import AnonymousUser
    from django.contrib.sessions.middleware import SessionMiddleware

    SessionMiddleware(lambda r: None).process_request(request)
    request.session.save()
    request.user = AnonymousUser()
    add_to_cart(request, product, 1)
    cart = get_or_create_cart(request)
    order = build_order_from_cart(
        cart=cart,
        email="cliente@example.com",
        shipping=SHIPPING,
        shipping_option_id="fixed-econ",
        user=None,
    )
    with pytest.raises(ValidationError):
        pay_order(order=order, payment_token="tok_fail")
    order.refresh_from_db()
    assert order.status == Order.Status.PAYMENT_FAILED
    product.stock.refresh_from_db()
    # reserva do carrinho permanece; disponível não baixou
    assert product.stock.quantity_available == 5


@pytest.mark.django_db
def test_refund(rf, product):
    request = rf.get("/")
    from django.contrib.auth.models import AnonymousUser
    from django.contrib.sessions.middleware import SessionMiddleware

    SessionMiddleware(lambda r: None).process_request(request)
    request.session.save()
    request.user = AnonymousUser()
    add_to_cart(request, product, 1)
    cart = get_or_create_cart(request)
    order = build_order_from_cart(
        cart=cart,
        email="a@b.com",
        shipping=SHIPPING,
        shipping_option_id="fixed-econ",
    )
    pay_order(order=order, payment_token="tok_ok")
    refund_order_payment(order)
    order.refresh_from_db()
    assert order.status == Order.Status.REFUNDED


@pytest.mark.django_db
def test_nfe_retry_on_failure(rf, product):
    request = rf.get("/")
    from django.contrib.auth.models import AnonymousUser
    from django.contrib.sessions.middleware import SessionMiddleware

    SessionMiddleware(lambda r: None).process_request(request)
    request.session.save()
    request.user = AnonymousUser()
    add_to_cart(request, product, 1)
    cart = get_or_create_cart(request)
    order = build_order_from_cart(
        cart=cart,
        email="a@b.com",
        shipping=SHIPPING,
        shipping_option_id="fixed-econ",
    )
    order.notes = "force_nfe_fail"
    order.save(update_fields=["notes"])
    pay_order(order=order, payment_token="tok_ok")
    inv = Invoice.objects.get(order=order)
    # eager celery retries may leave FAILED after max retries
    assert inv.status in {Invoice.Status.FAILED, Invoice.Status.ISSUED, Invoice.Status.PENDING}
    # limpa nota e reprocessa com sucesso
    order.notes = ""
    order.save(update_fields=["notes"])
    inv.status = Invoice.Status.PENDING
    inv.save(update_fields=["status"])
    emit_invoice_task(str(order.id))
    inv.refresh_from_db()
    assert inv.status == Invoice.Status.ISSUED
    assert inv.access_key


@pytest.mark.django_db
def test_checkout_views_flow(client, cart_ready):
    r = client.get(reverse("checkout:start"))
    assert r.status_code == 200
    r = client.post(reverse("checkout:start"), {**SHIPPING, "email": "c@example.com"})
    assert r.status_code == 302
    r = client.get(reverse("checkout:shipping"))
    assert r.status_code == 200
    assert b"PAC" in r.content or b"frete" in r.content.lower() or b"Correios" in r.content
    r = client.post(reverse("checkout:shipping"), {"shipping_option_id": "fixed-econ"})
    assert r.status_code == 302
    r = client.post(reverse("checkout:payment"), {"payment_token": "tok_sandbox_4242"})
    assert r.status_code == 302
    assert Order.objects.filter(status=Order.Status.PAID).exists()


@pytest.mark.django_db
def test_webhook_signature(client, rf, product):
    # cria pagamento pago com id conhecido
    request = rf.get("/")
    from django.contrib.auth.models import AnonymousUser
    from django.contrib.sessions.middleware import SessionMiddleware

    SessionMiddleware(lambda r: None).process_request(request)
    request.session.save()
    request.user = AnonymousUser()
    add_to_cart(request, product, 1)
    cart = get_or_create_cart(request)
    order = build_order_from_cart(
        cart=cart,
        email="w@example.com",
        shipping=SHIPPING,
        shipping_option_id="fixed-econ",
    )
    # força pending payment for webhook path
    Payment.objects.create(
        order=order,
        provider="mock",
        status=Payment.Status.PENDING,
        amount=order.total,
        provider_payment_id="mock_wh_1",
        payment_token="tok",
    )
    body = json.dumps({"provider_payment_id": "mock_wh_1", "status": "paid"}).encode()
    sig = hmac.new(b"dev-webhook-secret", body, hashlib.sha256).hexdigest()
    r = client.post(
        reverse("checkout:webhook"),
        data=body,
        content_type="application/json",
        HTTP_X_SIGNATURE=sig,
    )
    assert r.status_code == 200
    order.refresh_from_db()
    assert order.status == Order.Status.PAID


@pytest.mark.django_db
def test_webhook_rejects_bad_signature(client):
    body = b'{"status":"paid"}'
    r = client.post(
        reverse("checkout:webhook"),
        data=body,
        content_type="application/json",
        HTTP_X_SIGNATURE="invalid",
    )
    assert r.status_code == 400


@pytest.mark.django_db
def test_create_mercadopago_preference_mocked(settings):
    settings.PAYMENT_PROVIDER = "mercadopago"
    settings.MERCADOPAGO_CHECKOUT_MODE = "preference"
    settings.MERCADOPAGO_ACCESS_TOKEN = "TEST-token"
    settings.PUBLIC_BASE_URL = "https://shop.test"
    settings.DEBUG = True

    from unittest.mock import MagicMock, patch

    from apps.checkout.payments import create_mercadopago_preference

    mock_sdk = MagicMock()
    mock_sdk.preference.return_value.create.return_value = {
        "response": {
            "id": "pref-abc",
            "init_point": "https://www.mercadopago.com.br/checkout/v1/redirect?pref_id=pref-abc",
            "sandbox_init_point": "https://sandbox.mercadopago.com.br/checkout/v1/redirect?pref_id=pref-abc",
        }
    }
    with patch("mercadopago.SDK", return_value=mock_sdk):
        result = create_mercadopago_preference(
            order_number="ORD-1",
            order_id="00000000-0000-0000-0000-000000000001",
            amount=__import__("decimal").Decimal("119.90"),
            currency="BRL",
            title="Pedido ORD-1",
            payer_email="buyer@example.com",
        )
    assert result.success
    assert result.preference_id == "pref-abc"
    assert "sandbox" in result.checkout_url
    body = mock_sdk.preference.return_value.create.call_args[0][0]
    assert body["external_reference"] == "ORD-1"
    assert body["notification_url"].startswith("https://shop.test/")
    assert body["back_urls"]["success"].startswith("https://shop.test/checkout/sucesso/")
    assert body["auto_return"] == "approved"


@pytest.mark.django_db
def test_checkout_preference_redirects(client, cart_ready, settings):
    settings.PAYMENT_PROVIDER = "mercadopago"
    settings.MERCADOPAGO_CHECKOUT_MODE = "preference"
    settings.MERCADOPAGO_ACCESS_TOKEN = "TEST-token"
    settings.PUBLIC_BASE_URL = "https://shop.test"
    settings.DEBUG = True

    from unittest.mock import MagicMock, patch

    client.post(reverse("checkout:start"), {**SHIPPING, "email": "mp@example.com"})
    client.post(reverse("checkout:shipping"), {"shipping_option_id": "fixed-econ"})

    mock_sdk = MagicMock()
    mock_sdk.preference.return_value.create.return_value = {
        "response": {
            "id": "pref-xyz",
            "init_point": "https://www.mercadopago.com.br/checkout/v1/redirect?pref_id=pref-xyz",
            "sandbox_init_point": "https://sandbox.mercadopago.com.br/checkout/v1/redirect?pref_id=pref-xyz",
        }
    }
    with patch("mercadopago.SDK", return_value=mock_sdk):
        r = client.post(reverse("checkout:payment"))
    assert r.status_code == 302
    assert "mercadopago.com" in r["Location"]
    order = Order.objects.get()
    assert order.status == Order.Status.AWAITING_PAYMENT
    payment = order.payments.get()
    assert payment.provider_intent_id == "pref-xyz"
    assert payment.status == Payment.Status.PENDING


@pytest.mark.django_db
def test_mp_webhook_syncs_by_external_reference(client, rf, product, settings):
    settings.PAYMENT_PROVIDER = "mercadopago"
    settings.MERCADOPAGO_ACCESS_TOKEN = "TEST-token"

    from unittest.mock import patch

    from django.contrib.auth.models import AnonymousUser
    from django.contrib.sessions.middleware import SessionMiddleware

    request = rf.get("/")
    SessionMiddleware(lambda r: None).process_request(request)
    request.session.save()
    request.user = AnonymousUser()
    add_to_cart(request, product, 1)
    cart = get_or_create_cart(request)
    order = build_order_from_cart(
        cart=cart,
        email="mpw@example.com",
        shipping=SHIPPING,
        shipping_option_id="fixed-econ",
    )
    Payment.objects.create(
        order=order,
        provider=Payment.Provider.MERCADOPAGO,
        status=Payment.Status.PENDING,
        amount=order.total,
        provider_intent_id="pref-wh",
        payment_token="",
    )

    mp_payment = {
        "id": 987654321,
        "status": "approved",
        "external_reference": order.number,
        "preference_id": "pref-wh",
    }
    with patch(
        "apps.checkout.services.fetch_mercadopago_payment",
        return_value=mp_payment,
    ):
        r = client.get(
            reverse("checkout:webhook") + f"?topic=payment&id={mp_payment['id']}"
        )
    assert r.status_code == 200
    order.refresh_from_db()
    assert order.status == Order.Status.PAID
    payment = order.payments.get()
    assert payment.status == Payment.Status.PAID
    assert payment.provider_payment_id == "987654321"
