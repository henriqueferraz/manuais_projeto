"""Testes F4c — chamados e cross-sell."""

from __future__ import annotations

from datetime import timedelta

import pytest
from django.contrib.auth.models import User
from django.urls import reverse
from django.utils import timezone

from apps.catalog.models import Category
from apps.compatibility.models import Compatibility
from apps.products.models import Product, ProductTranslation, Stock
from apps.tickets.models import Ticket
from apps.tickets.services import check_sla_breaches, create_ticket, cross_sell_for_product
from apps.tickets.tasks import check_ticket_sla_task


@pytest.fixture
def products(db):
    cat = Category.objects.create(name="Peças", slug="pecas-xs")
    fan = Product.objects.create(
        sku="FAN-01",
        brand="Mondial",
        model_code="VTE-02",
        price="200",
        status=Product.Status.PUBLISHED,
        category=cat,
        product_kind=Product.Kind.FINISHED_GOOD,
    )
    ProductTranslation.objects.create(product=fan, locale="pt-BR", name="Ventilador")
    Stock.objects.create(product=fan, quantity_available=5)

    part = Product.objects.create(
        sku="PART-01",
        brand="Mondial",
        model_code="HEL",
        price="40",
        status=Product.Status.PUBLISHED,
        category=cat,
        product_kind=Product.Kind.SPARE_PART,
    )
    ProductTranslation.objects.create(product=part, locale="pt-BR", name="Hélice")
    Stock.objects.create(product=part, quantity_available=10)
    Compatibility.objects.create(
        equipment_brand="Mondial", equipment_model="VTE-02", part_product=part
    )
    return fan, part


@pytest.mark.django_db
def test_create_and_list_ticket(client):
    r = client.post(
        reverse("tickets:list"),
        {
            "email": "cli@example.com",
            "title": "Barulho no ventilador",
            "equipment": "VTE-02",
            "description": "Faz barulho ao ligar",
            "priority": "medium",
        },
    )
    assert r.status_code == 302
    ticket = Ticket.objects.get()
    assert ticket.code.startswith("CH-")
    r2 = client.get(reverse("tickets:list"), {"email": "cli@example.com"})
    assert ticket.code.encode() in r2.content


@pytest.mark.django_db
def test_support_updates_status(client):
    user = User.objects.create_user("sup", password="x", is_staff=True)
    ticket = create_ticket(email="a@b.com", title="T", description="D", equipment="X", user=None)
    client.force_login(user)
    r = client.post(
        reverse("tickets:update_status", kwargs={"code": ticket.code}),
        {"status": "in_analysis", "note": "Analisando"},
    )
    assert r.status_code == 302
    ticket.refresh_from_db()
    assert ticket.status == Ticket.Status.IN_ANALYSIS
    assert ticket.events.count() >= 2


@pytest.mark.django_db
def test_sla_breach_alert():
    ticket = create_ticket(email="a@b.com", title="SLA", description="x")
    Ticket.objects.filter(pk=ticket.pk).update(
        sla_due_at=timezone.now() - timedelta(hours=1),
        sla_breached=False,
    )
    n = check_sla_breaches()
    assert n == 1
    ticket.refresh_from_db()
    assert ticket.sla_breached is True
    assert check_ticket_sla_task()["breached"] == 0  # já marcado


@pytest.mark.django_db
def test_cross_sell_on_pdp(client, products):
    fan, part = products
    r = client.get(reverse("catalog:detail", kwargs={"slug": fan.slug}))
    assert r.status_code == 200
    assert b"PART-01" in r.content or b"H" in r.content
    assert part in cross_sell_for_product(fan)
