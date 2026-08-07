"""Testes T-P.4 — integrações live com mocks (CI permanece sem rede)."""

from __future__ import annotations

from decimal import Decimal
from unittest.mock import MagicMock, patch

import pytest

from apps.checkout.nfe import emit_nfe
from apps.checkout.shipping import calculate_shipping
from apps.subscriptions.billing import start_subscription
from apps.subscriptions.models import SubscriptionPlan


@pytest.mark.django_db
def test_nfe_mock_emits_access_key(product_order_factory=None):
    from apps.catalog.models import Category
    from apps.orders.models import Invoice, Order, OrderItem
    from apps.products.models import Product

    cat = Category.objects.create(name="X", slug="x-nfe")
    product = Product.objects.create(
        sku="NFE-1",
        brand="B",
        model_code="M",
        price="10.00",
        status=Product.Status.PUBLISHED,
        category=cat,
    )
    order = Order.objects.create(
        number=Order.next_number(),
        email="a@b.com",
        shipping_name="A",
        shipping_cep="01310100",
        shipping_street="Rua",
        shipping_number="1",
        shipping_district="B",
        shipping_city="SP",
        shipping_state="SP",
        subtotal=Decimal("10.00"),
        total=Decimal("10.00"),
        status=Order.Status.PAID,
    )
    OrderItem.objects.create(
        order=order,
        product=product,
        sku=product.sku,
        name="Peça",
        quantity=1,
        unit_price=Decimal("10.00"),
        line_total=Decimal("10.00"),
    )
    invoice = Invoice.objects.create(order=order)
    result = emit_nfe(order, invoice)
    assert len(result["access_key"]) == 44
    assert result["provider"] == "mock"


@pytest.mark.django_db
def test_nfe_focus_requires_token(settings):
    from apps.orders.models import Invoice, Order

    settings.NFE_PROVIDER = "focusnfe"
    settings.FOCUSNFE_TOKEN = ""
    order = Order.objects.create(
        number=Order.next_number(),
        email="a@b.com",
        shipping_name="A",
        shipping_cep="01310100",
        shipping_street="Rua",
        shipping_number="1",
        shipping_district="B",
        shipping_city="SP",
        shipping_state="SP",
        subtotal=Decimal("10.00"),
        total=Decimal("10.00"),
    )
    invoice = Invoice.objects.create(order=order)
    with pytest.raises(RuntimeError, match="FOCUSNFE_TOKEN"):
        emit_nfe(order, invoice)


@pytest.mark.django_db
def test_melhor_envio_stub(settings):
    settings.MELHOR_ENVIO_ENABLED = True
    settings.MELHOR_ENVIO_TOKEN = "tok"
    settings.MELHOR_ENVIO_STUB = True
    opts = calculate_shipping(cep="01310100", subtotal=Decimal("50"))
    assert opts[0].source == "melhor_envio"


@pytest.mark.django_db
def test_subscription_billing_mock():
    plan = SubscriptionPlan.objects.create(
        code="basic",
        name="Básico",
        price_monthly=Decimal("29.90"),
    )
    result = start_subscription(plan=plan, email="x@y.com")
    assert result.success
    assert result.subscription is not None
    assert result.subscription.billing_provider == "mock"


def test_whatsapp_live_posts_graph(settings):
    from apps.channels.views import _send_outbound

    settings.WHATSAPP_MODE = "live"
    settings.WHATSAPP_ACCESS_TOKEN = "tok"
    settings.WHATSAPP_PHONE_NUMBER_ID = "123"
    fake_resp = MagicMock()
    fake_resp.read.return_value = b'{"messages":[{"id":"wamid.1"}]}'
    fake_resp.__enter__.return_value = fake_resp
    fake_resp.__exit__.return_value = False
    with patch("urllib.request.urlopen", return_value=fake_resp) as mocked:
        _send_outbound("5511999999999", "olá")
        assert mocked.called
