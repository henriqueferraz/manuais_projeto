"""Testes F4d — cupons, promoções e trocas/devoluções CDC."""

from __future__ import annotations

from datetime import timedelta
from decimal import Decimal

import pytest
from apps.cart.coupons import apply_coupon_code, cart_totals_with_coupon, effective_price
from apps.cart.models import Coupon, ProductPromotion
from apps.cart.services import add_to_cart, get_or_create_cart
from apps.catalog.models import Category
from apps.checkout.services import build_order_from_cart, pay_order
from apps.orders.models import Order, Payment, ReturnRequest
from apps.orders.return_services import create_return_request, process_return
from apps.products.models import Product, ProductTranslation, Stock
from django.contrib.auth import get_user_model
from django.core.exceptions import ValidationError
from django.urls import reverse
from django.utils import timezone

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


@pytest.fixture
def product(db):
    cat = Category.objects.create(name="Peças", slug="pecas-f4d")
    p = Product.objects.create(
        sku="CPN-001",
        brand="Mondial",
        model_code="X1",
        price="200.00",
        status=Product.Status.PUBLISHED,
        category=cat,
        weight_kg="1.0",
    )
    ProductTranslation.objects.create(product=p, locale="pt-BR", name="Peça cupom")
    Stock.objects.create(product=p, quantity_available=10, quantity_reserved=0)
    return p


@pytest.fixture
def percent_coupon(db):
    return Coupon.objects.create(
        code="DESC10",
        kind=Coupon.Kind.PERCENT,
        value=Decimal("10"),
        min_subtotal=Decimal("0"),
        active=True,
    )


@pytest.mark.django_db
def test_apply_valid_coupon(percent_coupon):
    coupon, discount = apply_coupon_code("desc10", subtotal=Decimal("200.00"))
    assert coupon.code == "DESC10"
    assert discount == Decimal("20.00")


@pytest.mark.django_db
def test_apply_invalid_coupon():
    with pytest.raises(ValidationError, match="inválido"):
        apply_coupon_code("NAOEXISTE", subtotal=Decimal("50"))


@pytest.mark.django_db
def test_coupon_expired():
    Coupon.objects.create(
        code="OLD",
        kind=Coupon.Kind.FIXED,
        value=Decimal("10"),
        valid_until=timezone.now() - timedelta(days=1),
        active=True,
    )
    with pytest.raises(ValidationError, match="expirado"):
        apply_coupon_code("OLD", subtotal=Decimal("50"))


@pytest.mark.django_db
def test_cart_totals_with_coupon(rf, product, percent_coupon):
    request = rf.get("/")
    from django.contrib.auth.models import AnonymousUser
    from django.contrib.sessions.middleware import SessionMiddleware

    SessionMiddleware(lambda r: None).process_request(request)
    request.session.save()
    request.user = AnonymousUser()
    add_to_cart(request, product, 1)
    cart = get_or_create_cart(request)
    totals = cart_totals_with_coupon(cart, "DESC10")
    assert totals["subtotal"] == Decimal("200.00")
    assert totals["discount"] == Decimal("20.00")
    assert totals["total_after_discount"] == Decimal("180.00")


@pytest.mark.django_db
def test_promo_price(product):
    now = timezone.now()
    ProductPromotion.objects.create(
        product=product,
        promo_price=Decimal("150.00"),
        valid_from=now - timedelta(hours=1),
        valid_until=now + timedelta(days=1),
        active=True,
    )
    assert effective_price(product) == Decimal("150.00")


@pytest.mark.django_db
def test_checkout_applies_coupon(rf, product, percent_coupon):
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
        coupon_code="DESC10",
    )
    assert order.discount == Decimal("20.00")
    assert order.coupon_code == "DESC10"
    assert order.subtotal == Decimal("200.00")
    assert order.total == order.subtotal - order.discount + order.shipping_cost
    percent_coupon.refresh_from_db()
    assert percent_coupon.used_count == 1


@pytest.mark.django_db
def test_coupon_htmx_apply(client, product, percent_coupon):
    client.post(reverse("cart:add"), {"product_id": product.pk, "quantity": 1})
    resp = client.post(reverse("cart:apply_coupon"), {"code": "DESC10"})
    assert resp.status_code == 302
    assert client.session.get("coupon_code") == "DESC10"
    resp = client.post(reverse("cart:apply_coupon"), {"code": "FALSO"})
    assert resp.status_code == 302
    assert "coupon_code" not in client.session or client.session.get("coupon_code") in ("", None)


@pytest.mark.django_db
def test_return_regret_within_window_and_refund(rf, product):
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
    )
    pay_order(order=order, payment_token="tok_sandbox_4242")
    order.refresh_from_db()
    assert order.status == Order.Status.PAID

    ret = create_return_request(
        order=order,
        email="cliente@example.com",
        kind=ReturnRequest.Kind.REFUND,
        reason=ReturnRequest.Reason.REGRET,
        details="Mudança de ideia",
    )
    assert ret.status == ReturnRequest.Status.REQUESTED
    assert ret.within_cdc_window

    process_return(ret, approve=True, staff_notes="ok")
    ret.refresh_from_db()
    assert ret.status == ReturnRequest.Status.REFUNDED
    assert Payment.objects.filter(order=order, status=Payment.Status.REFUNDED).exists()


@pytest.mark.django_db
def test_return_regret_expired(rf, product):
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
    )
    pay_order(order=order, payment_token="tok_sandbox_4242")
    order.refresh_from_db()

    with pytest.raises(ValidationError, match="Prazo"):
        create_return_request(
            order=order,
            email="cliente@example.com",
            kind=ReturnRequest.Kind.REFUND,
            reason=ReturnRequest.Reason.REGRET,
            delivered_at=timezone.now() - timedelta(days=10),
        )


@pytest.mark.django_db
def test_returns_ops_requires_staff(client, product):
    User = get_user_model()
    user = User.objects.create_user(username="cli", password="x", email="c@ex.com")
    client.force_login(user)
    resp = client.get(reverse("returns:ops"))
    assert resp.status_code in {302, 403}
