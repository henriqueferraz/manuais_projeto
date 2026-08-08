"""Testes do dashboard F7."""

from __future__ import annotations

from decimal import Decimal

import pytest
from django.contrib.auth import get_user_model
from django.core import mail
from django.core.files.base import ContentFile
from django.test import Client
from django.urls import reverse

from apps.ai.models import ChatFeedback, ChatMessage, ChatSession
from apps.dashboard.models import OpsAlert
from apps.dashboard.services.metrics import collect_insights
from apps.dashboard.services.monitoring import collect_monitoring, simulate_incident
from apps.manuals.models import ExtractionLog, Manual
from apps.orders.models import Order
from apps.tickets.models import Ticket, TicketEvent

User = get_user_model()


@pytest.fixture
def staff_user(db):
    return User.objects.create_user(
        username="ops",
        email="ops@example.com",
        password="x",
        is_staff=True,
    )


@pytest.mark.django_db
def test_insights_four_areas(staff_user):
    session = ChatSession.objects.create(anonymous_key="d7")
    ChatMessage.objects.create(
        session=session,
        role=ChatMessage.Role.USER,
        content="Qual o capacitor de partida?",
    )
    asst = ChatMessage.objects.create(
        session=session,
        role=ChatMessage.Role.ASSISTANT,
        content="Com base no manual...",
        found_in_manual=True,
        cost_estimate=Decimal("0.002"),
        tokens_in=10,
        tokens_out=20,
    )
    ChatFeedback.objects.create(message=asst, vote=ChatFeedback.Vote.UP)

    ticket = Ticket.objects.create(
        code="TK-TEST-1",
        email="c@ex.com",
        title="Barulho",
        description="faz barulho",
        origin=Ticket.Origin.CHAT,
        status=Ticket.Status.RESOLVED,
    )
    TicketEvent.objects.create(
        ticket=ticket,
        status_from=Ticket.Status.OPEN,
        status_to=Ticket.Status.RESOLVED,
        note="ok",
    )

    Order.objects.create(
        number="TP-TEST-1",
        email="c@ex.com",
        shipping_name="A",
        shipping_cep="01310100",
        shipping_street="R",
        shipping_number="1",
        shipping_district="B",
        shipping_city="SP",
        shipping_state="SP",
        subtotal=Decimal("100"),
        total=Decimal("100"),
        attribution_source=Order.AttributionSource.DIAGNOSIS,
        chat_session=session,
    )

    manual = Manual(
        original_filename="x.pdf",
        mime_type="application/pdf",
        scan_status=Manual.ScanStatus.SKIPPED,
    )
    manual.file.save("x.pdf", ContentFile(b"%PDF-1.4\n%%EOF\n"), save=False)
    manual.compute_and_set_sha256(b"%PDF-1.4\n%%EOF\n")
    manual.save()
    ExtractionLog.objects.create(
        manual=manual,
        status=ExtractionLog.Status.APPROVED,
        cost_estimate=Decimal("0.01"),
    )

    payload = collect_insights(days=30)
    assert payload.chat["sessions"] >= 1
    assert payload.chat["feedback_up"] >= 1
    assert payload.tickets["total"] >= 1
    assert payload.sales_ai["ai_influenced_orders"] >= 1
    assert payload.ai_cost["total_usd"] > 0

    client = Client()
    client.force_login(staff_user)
    res = client.get(reverse("dashboard:insights"))
    assert res.status_code == 200
    body = res.content.decode()
    assert "Chat / RAG" in body
    assert "Chamados" in body
    assert "Vendas influenciadas" in body
    assert "Custo de IA" in body


@pytest.mark.django_db
def test_monitoring_simulated_incident_appears(staff_user, settings):
    settings.OPS_ALERT_EMAILS = ["ops@example.com"]
    settings.EMAIL_BACKEND = "django.core.mail.backends.locmem.EmailBackend"
    mail.outbox.clear()

    alert = simulate_incident(title="Incidente simulado teste")
    assert alert.pk
    assert OpsAlert.objects.filter(pk=alert.pk, acknowledged=False).exists()
    assert mail.outbox  # e-mail de alerta

    snap = collect_monitoring()
    assert any(a["title"] == "Incidente simulado teste" for a in snap.alerts)

    client = Client()
    client.force_login(staff_user)
    res = client.get(reverse("dashboard:monitoring"))
    assert res.status_code == 200
    assert b"Incidente simulado teste" in res.content

    res2 = client.post(reverse("dashboard:simulate_incident"))
    assert res2.status_code in (302, 200)


@pytest.mark.django_db
def test_insights_requires_staff(client):
    res = client.get(reverse("dashboard:insights"))
    assert res.status_code in (302, 301)


@pytest.mark.django_db
def test_home_hero_dashboard_staff_ok(staff_user):
    from apps.dashboard.models import HomeHeroSlide

    HomeHeroSlide.objects.create(title="Slide A", sort_order=0, is_active=True)
    client = Client()
    client.force_login(staff_user)
    res = client.get(reverse("dashboard:home_hero"))
    assert res.status_code == 200
    assert b"Hero da home" in res.content
    assert b"Slide A" in res.content


@pytest.mark.django_db
def test_home_hero_dashboard_anonymous_redirects(client):
    res = client.get(reverse("dashboard:home_hero"))
    assert res.status_code in (302, 301)


@pytest.mark.django_db
def test_home_hero_create_slide(staff_user):
    from apps.dashboard.models import HomeHeroSlide

    client = Client()
    client.force_login(staff_user)
    res = client.post(
        reverse("dashboard:home_hero_create"),
        {
            "badge": "ESTOQUE",
            "title": "Alta Performance",
            "lead": "Componentes certificados.",
            "alt_text": "",
            "sort_order": 1,
            "is_active": "on",
        },
    )
    assert res.status_code == 302
    slide = HomeHeroSlide.objects.get(title="Alta Performance")
    assert slide.badge == "ESTOQUE"
    assert slide.is_active


@pytest.mark.django_db
def test_products_dashboard_staff_ok(staff_user):
    from decimal import Decimal

    from apps.catalog.models import Category
    from apps.products.models import Product, ProductTranslation, Stock

    cat = Category.objects.create(name="Ventiladores", slug="vent-dash")
    product = Product.objects.create(
        sku="DASH-01",
        brand="Mondial",
        model_code="D1",
        price=Decimal("50.00"),
        status=Product.Status.PUBLISHED,
        category=cat,
    )
    ProductTranslation.objects.create(product=product, locale="pt-BR", name="Peça dashboard")
    Stock.objects.create(product=product, quantity_available=4, minimum_alert=2)

    client = Client()
    client.force_login(staff_user)
    res = client.get(reverse("dashboard:products"))
    assert res.status_code == 200
    assert b"Estoque e produtos" in res.content
    assert b"DASH-01" in res.content
    assert b"Pe" in res.content


@pytest.mark.django_db
def test_products_dashboard_create(staff_user, db):
    from apps.catalog.models import Brand, Category, EquipmentModel
    from apps.products.models import Product, Stock

    cat = Category.objects.create(name="Cat dash", slug="cat-dash")
    brand = Brand.objects.create(name="LG", slug="lg")
    model = EquipmentModel.objects.create(code="L1", brand="LG", slug="lg-l1")
    client = Client()
    client.force_login(staff_user)
    res = client.post(
        reverse("dashboard:products_create"),
        {
            "sku": "DASH-NEW",
            "brand_ref": brand.pk,
            "equipment_model": model.pk,
            "name": "Compressor teste",
            "description": "",
            "price": "199.90",
            "voltage": "110V",
            "product_kind": "spare_part",
            "status": "draft",
            "category": cat.pk,
            "quantity_available": 5,
            "minimum_alert": 1,
        },
    )
    assert res.status_code == 302
    product = Product.objects.get(sku="DASH-NEW")
    assert product.brand == "LG"
    assert product.brand_ref_id == brand.pk
    assert product.model_code == "L1"
    assert product.equipment_model_id == model.pk
    assert Stock.objects.get(product=product).quantity_available == 5


@pytest.mark.django_db
def test_products_dashboard_delete(staff_user):
    from decimal import Decimal

    from apps.products.models import Product

    product = Product.objects.create(
        sku="DASH-DEL",
        brand="Mondial",
        model_code="X",
        price=Decimal("10.00"),
        status=Product.Status.DRAFT,
    )
    client = Client()
    client.force_login(staff_user)
    res = client.post(reverse("dashboard:products_delete", args=[product.pk]))
    assert res.status_code == 302
    assert not Product.objects.filter(sku="DASH-DEL").exists()


@pytest.mark.django_db
def test_products_edit_shows_and_saves_specs(staff_user, db):
    from decimal import Decimal

    from apps.catalog.models import Brand, Category
    from apps.products.models import Product, ProductTranslation, Stock

    brand = Brand.objects.create(name="SpecsBrand", slug="specsbrand")
    cat = Category.objects.create(name="SpecsCat", slug="specs-cat")
    product = Product.objects.create(
        sku="SPEC-01",
        brand="SpecsBrand",
        brand_ref=brand,
        price=Decimal("20.00"),
        status=Product.Status.DRAFT,
        category=cat,
        power_w=Decimal("120.00"),
        weight_kg=Decimal("2.500"),
        dimensions={"height_cm": 40, "width_cm": 30, "depth_cm": 20},
        specs={"blade_count": 3, "material": "ABS", "ncm": "84145910"},
    )
    ProductTranslation.objects.create(product=product, locale="pt-BR", name="Produto specs")
    Stock.objects.create(product=product, quantity_available=2, minimum_alert=1)

    client = Client()
    client.force_login(staff_user)
    get_res = client.get(reverse("dashboard:products_edit", args=[product.pk]))
    assert get_res.status_code == 200
    assert b"Especifica" in get_res.content
    assert b"value=\"120\"" in get_res.content or b"value=\"120.00\"" in get_res.content
    assert b"ABS" in get_res.content
    assert b"ncm: 84145910" in get_res.content

    post_res = client.post(
        reverse("dashboard:products_edit", args=[product.pk]),
        {
            "sku": "SPEC-01",
            "brand_ref": brand.pk,
            "name": "Produto specs",
            "description": "",
            "price": "20.00",
            "voltage": "220V",
            "product_kind": "finished_good",
            "status": "draft",
            "category": cat.pk,
            "quantity_available": 2,
            "minimum_alert": 1,
            "power_w": "150",
            "weight_kg": "3.1",
            "dim_height_cm": "41",
            "dim_width_cm": "31",
            "dim_depth_cm": "21",
            "blade_count": "4",
            "diameter_cm": "40",
            "material": "PP",
            "color": "preto",
            "rpm": "1350",
            "mounting": "mesa",
            "bearing_type": "esferas",
            "remote_included": "on",
            "specs_extra": "ncm: 84145990",
        },
    )
    assert post_res.status_code == 302
    product.refresh_from_db()
    assert product.power_w == Decimal("150.00")
    assert product.weight_kg == Decimal("3.100")
    assert product.dimensions == {"height_cm": 41.0, "width_cm": 31.0, "depth_cm": 21.0}
    assert product.specs["blade_count"] == 4
    assert product.specs["material"] == "PP"
    assert product.specs["remote_included"] is True
    assert product.specs["ncm"] == 84145990
