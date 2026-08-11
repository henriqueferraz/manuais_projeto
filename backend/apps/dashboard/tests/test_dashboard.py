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
    assert b'value="120"' in get_res.content or b'value="120.00"' in get_res.content
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


def _pdf_bytes(extra: bytes = b"") -> bytes:
    return b"%PDF-1.4\n1 0 obj<<>>endobj\ntrailer<<>>\n%%EOF\n" + extra


@pytest.mark.django_db
def test_products_create_shows_ai_pdf_upload(staff_user):
    client = Client()
    client.force_login(staff_user)
    res = client.get(reverse("dashboard:products_create"))
    assert res.status_code == 200
    assert b"product-ai-assist" in res.content
    assert b"Assistente IA" in res.content
    assert b"Antiv" in res.content
    assert b'accept=".pdf,application/pdf"' in res.content


@pytest.mark.django_db
def test_products_ai_extract_requires_antivirus_and_awaits_approval(
    staff_user, monkeypatch, settings
):
    settings.EXTRACTION_LLM_MODE = "mock"
    settings.CELERY_TASK_ALWAYS_EAGER = True

    from apps.manuals.validators import EICAR_SIGNATURE
    from apps.products.models import Product

    client = Client()
    client.force_login(staff_user)

    # Antivírus bloqueia EICAR
    bad = client.post(
        reverse("dashboard:products_ai_extract"),
        {"manual": ContentFile(_pdf_bytes(EICAR_SIGNATURE), name="evil.pdf")},
    )
    assert bad.status_code == 400
    assert bad.json()["ok"] is False
    assert "antiv" in bad.json()["error"].lower() or "malicios" in bad.json()["error"].lower()

    sample_text = (
        "Mondial\nVentilador de Teto\nModelo: VTE-02\nPotência: 120 W\n"
        "Voltagem: Bivolt 127/220V\n"
    )

    class FakePdf:
        text = sample_text
        page_count = 1
        used_ocr = False
        tables = []

    monkeypatch.setattr(
        "apps.manuals.graphs.extraction.extract_pdf_text",
        lambda content, **kwargs: FakePdf(),
    )

    ok = client.post(
        reverse("dashboard:products_ai_extract"),
        {"manual": ContentFile(_pdf_bytes(), name="Manual-VTE-02.pdf")},
    )
    assert ok.status_code == 200
    payload = ok.json()
    assert payload["ok"] is True
    assert payload["awaiting_approval"] is True
    assert payload["extraction_id"]
    assert payload["form_suggestions"]["name"]
    assert "VTE-02" in (payload["extracted"].get("model_code") or "")
    sug = payload["form_suggestions"]
    assert sug.get("brand_ref"), "marca deve ser criada/resolvida para o select"
    assert sug.get("brand_name")
    assert sug.get("equipment_model"), "modelo deve ser criado/resolvido para o select"
    assert sug.get("description") or payload["extracted"].get("description") is not None
    from apps.catalog.models import Brand, EquipmentModel

    assert Brand.objects.filter(pk=sug["brand_ref"]).exists()
    assert EquipmentModel.objects.filter(pk=sug["equipment_model"]).exists()

    # Não criou produto ainda
    assert not Product.objects.filter(sku__icontains="VTE").exists()
    log = ExtractionLog.objects.get(pk=payload["extraction_id"])
    assert log.status == ExtractionLog.Status.AWAITING_REVIEW

    # Descartar
    discard = client.post(reverse("dashboard:products_ai_discard", args=[payload["extraction_id"]]))
    assert discard.status_code == 200
    log.refresh_from_db()
    assert log.status == ExtractionLog.Status.REJECTED


@pytest.mark.django_db
def test_build_form_suggestions_creates_missing_catalog_refs():
    from apps.catalog.models import Brand, Category, EquipmentModel
    from apps.dashboard.services.product_ai_assist import build_form_suggestions
    from apps.manuals.schemas import ExtractedProduct

    schema = ExtractedProduct(
        brand="NovaMarcaX",
        model_code="NM-100",
        name="Aparelho teste",
        description="Descrição proposta pela IA.",
        category="Categoria Nova Y",
        voltage="220V",
    )
    sug = build_form_suggestions(schema)
    assert sug["brand_ref"] == Brand.objects.get(name="NovaMarcaX").pk
    assert sug["category"] == Category.objects.get(name="Categoria Nova Y").pk
    assert sug["equipment_model"] == EquipmentModel.objects.get(code="NM-100").pk
    assert sug["description"] == "Descrição proposta pela IA."
    # Sem descrição → gera texto de venda
    schema2 = ExtractedProduct(
        brand="NovaMarcaX",
        model_code="NM-101",
        name="Aparelho sem descrição",
        description="",
        category="Categoria Nova Y",
        voltage="110V",
    )
    sug_empty = build_form_suggestions(schema2)
    assert sug_empty["description"]
    assert len([ln for ln in sug_empty["description"].splitlines() if ln.strip()]) <= 4
    # Idempotente
    sug2 = build_form_suggestions(schema)
    assert sug2["brand_ref"] == sug["brand_ref"]
    assert Brand.objects.filter(name="NovaMarcaX").count() == 1


@pytest.mark.django_db
def test_prepare_product_image_rejects_eicar(settings):
    from django.core.exceptions import ValidationError
    from django.core.files.uploadedfile import SimpleUploadedFile

    from apps.manuals.validators import EICAR_SIGNATURE
    from apps.products.image_validation import prepare_product_image

    upload = SimpleUploadedFile(
        "evil.jpg",
        EICAR_SIGNATURE + b"\xff\xd8\xff",
        content_type="image/jpeg",
    )
    with pytest.raises(ValidationError, match="antiv|malicios"):
        prepare_product_image(upload)


def _blank_pdf_bytes() -> bytes:
    from io import BytesIO

    from pypdf import PdfWriter

    writer = PdfWriter()
    writer.add_blank_page(width=400, height=400)
    buf = BytesIO()
    writer.write(buf)
    return buf.getvalue()


@pytest.mark.django_db
def test_parts_for_review_marks_sellable_only():
    from apps.dashboard.services.product_ai_assist import parts_for_review
    from apps.manuals.schemas import ExtractedProduct, RelatedPartHint

    schema = ExtractedProduct(
        brand="Philco",
        model_code="PB120N",
        name="Rádio",
        spare_parts=[
            RelatedPartHint(
                code="706452",
                name="Alto-falante",
                sellable_separately=True,
                sku_suggestion="PHILCO-706452",
            ),
            RelatedPartHint(
                code="",
                name="Embalagem",
                sellable_separately=True,  # sem code → false após validator
            ),
        ],
        accessories=[
            RelatedPartHint(
                code="ACC-1",
                name="Controle",
                sellable_separately=True,
                sku_suggestion="PHILCO-ACC-1",
            ),
        ],
    )
    rows = parts_for_review(schema)
    assert len(rows) == 3
    by_code = {r["code"]: r for r in rows}
    assert by_code["706452"]["selected"] is True
    assert by_code["706452"]["sellable_separately"] is True
    assert by_code[""]["selected"] is False
    assert by_code[""]["sellable_separately"] is False
    assert by_code["ACC-1"]["kind"] == "accessory"


@pytest.mark.django_db
def test_pdf_cover_render_and_link_materializes_selected_parts(
    staff_user, settings, tmp_path, django_capture_on_commit_callbacks
):
    settings.EXTRACTION_LLM_MODE = "mock"
    settings.CELERY_TASK_ALWAYS_EAGER = True
    settings.MEDIA_ROOT = tmp_path
    settings.MANUAL_AV_STUB_OK = True

    from unittest.mock import patch

    from django.core.files.base import ContentFile

    from apps.compatibility.models import Compatibility
    from apps.dashboard.services.product_ai_assist import (
        attach_manual_cover_as_product_image,
        link_approved_extraction_to_product,
        related_spare_parts_for_product,
    )
    from apps.manuals.models import ExtractionLog, Manual
    from apps.manuals.services.pdf_cover import render_pdf_first_page_jpeg
    from apps.products.models import Product, ProductImage, ProductTranslation

    jpeg = render_pdf_first_page_jpeg(_blank_pdf_bytes())
    assert jpeg is not None
    assert jpeg[:2] == b"\xff\xd8"

    manual = Manual.objects.create(
        original_filename="capa.pdf",
        mime_type="application/pdf",
        manufacturer="Philco",
        sha256="b" * 64,
        size_bytes=100,
        scan_status="skipped",
    )
    manual.file.save("capa.pdf", ContentFile(_blank_pdf_bytes()), save=True)

    log = ExtractionLog.objects.create(
        manual=manual,
        status=ExtractionLog.Status.AWAITING_REVIEW,
        prompt_version="v3",
        raw_json={
            "brand": "Philco",
            "model_code": "PB120N",
            "name": "Rádio CD Player",
            "sku_suggestion": "PHILCO-PB120N",
            "product_kind": "finished_good",
            "spare_parts": [
                {
                    "code": "706452",
                    "name": "Alto-falante",
                    "sku_suggestion": "PHILCO-706452",
                    "sellable_separately": True,
                    "compatible_with": ["PB120N"],
                },
                {
                    "code": "706999",
                    "name": "Botão",
                    "sku_suggestion": "PHILCO-706999",
                    "sellable_separately": True,
                    "compatible_with": ["PB120N"],
                },
            ],
            "accessories": [],
            "confidence": 0.9,
        },
    )

    product = Product.objects.create(
        sku="PHILCO-PB120N",
        brand="Philco",
        model_code="PB120N",
        product_kind=Product.Kind.FINISHED_GOOD,
        status=Product.Status.DRAFT,
        price=0,
    )
    ProductTranslation.objects.create(
        product=product, locale="pt-BR", name="Rádio CD Player", slug="radio-pb120n"
    )

    with patch("apps.ai.tasks.index_manual_task.delay") as mock_delay:
        with django_capture_on_commit_callbacks(execute=True):
            result = link_approved_extraction_to_product(
                extraction_id=log.pk,
                product=product,
                user=staff_user,
                selected_part_codes={"706452"},
            )
        mock_delay.assert_called_once_with(manual.pk)

    assert result is not None
    assert result["cover_attached"] is True
    assert result["parts_created"] == 1
    assert ProductImage.objects.filter(product=product, is_primary=True).exists()
    assert Product.objects.filter(sku="PHILCO-706452").exists()
    assert not Product.objects.filter(sku="PHILCO-706999").exists()
    assert Compatibility.objects.filter(part_product__sku="PHILCO-706452").exists()

    related = related_spare_parts_for_product(product)
    assert len(related) == 1
    assert related[0].sku == "PHILCO-706452"
    assert related[0].model_code == "PB120N"
    assert related[0].category.name == "Peça de reposição"
    assert related[0].specs.get("part_code") == "706452"

    # Segunda chamada não duplica capa
    assert attach_manual_cover_as_product_image(product, manual) is None


@pytest.mark.django_db
def test_products_edit_lists_related_parts_with_modal(staff_user, db):
    from apps.compatibility.models import Compatibility
    from apps.products.models import Product, ProductTranslation

    client = Client()
    client.force_login(staff_user)

    parent = Product.objects.create(
        sku="EQ-1",
        brand="Mondial",
        model_code="VTE-02",
        product_kind=Product.Kind.FINISHED_GOOD,
        status=Product.Status.DRAFT,
        price=100,
    )
    ProductTranslation.objects.create(
        product=parent, locale="pt-BR", name="Ventilador", slug="ventilador-vte-02"
    )
    part = Product.objects.create(
        sku="MONDIAL-CAP",
        brand="Mondial",
        model_code="VTE-02",
        product_kind=Product.Kind.SPARE_PART,
        status=Product.Status.DRAFT,
        price=20,
        specs={"parent_sku": "EQ-1", "part_code": "CAP-1"},
    )
    ProductTranslation.objects.create(
        product=part, locale="pt-BR", name="Capacitor", slug="capacitor-cap-1"
    )
    Compatibility.objects.create(
        equipment_brand="Mondial",
        equipment_model="VTE-02",
        part_product=part,
    )

    res = client.get(reverse("dashboard:products_edit", args=[parent.pk]))
    assert res.status_code == 200
    assert "Peças de reposição vinculadas".encode() in res.content
    assert b"Capacitor" in res.content
    assert b"related-part-modal" in res.content
    assert b"related-parts-data" in res.content
    assert b'target="_blank"' not in res.content
    assert b"data-related-part-id" in res.content
    assert str(part.pk).encode() in res.content


@pytest.mark.django_db
def test_products_ai_extract_returns_parts_for_review(staff_user, monkeypatch, settings):
    settings.EXTRACTION_LLM_MODE = "mock"
    settings.CELERY_TASK_ALWAYS_EAGER = True
    settings.MANUAL_AV_STUB_OK = True

    client = Client()
    client.force_login(staff_user)

    sample_text = (
        "Philco\nRádio PB120N\nModelo: PB120N\n"
        "207 1000014182 QUEIMADOR 1,7 KW ALTA 4\n"
        "208 1000014183 INJETOR GLP 1\n"
        "Embalagem caixa externa\n"
    )

    class FakePdf:
        text = sample_text
        page_count = 1
        used_ocr = False
        tables = []

    monkeypatch.setattr(
        "apps.manuals.graphs.extraction.extract_pdf_text",
        lambda content, **kwargs: FakePdf(),
    )

    ok = client.post(
        reverse("dashboard:products_ai_extract"),
        {"manual": ContentFile(_pdf_bytes(), name="parts.pdf")},
    )
    assert ok.status_code == 200
    payload = ok.json()
    assert payload["ok"] is True
    assert "parts_for_review" in payload
    sellable = [p for p in payload["parts_for_review"] if p.get("sellable_separately")]
    assert sellable
    assert b"product-ai-parts" not in ok.content  # JSON API, painel é no HTML
    html = client.get(reverse("dashboard:products_create"))
    assert b"product-ai-parts" in html.content
    assert b"id_selected_part_codes" in html.content
    assert b"product-ai-model-picker" in html.content
    assert b"product-ai-sections" in html.content


@pytest.mark.django_db
def test_specs_extra_includes_warranty_warnings_usage_variants():
    from apps.dashboard.services.product_ai_assist import (
        _specs_extra_lines,
        build_form_suggestions,
        build_proposal_sections,
        collect_model_options,
    )
    from apps.manuals.schemas import ExtractedProduct, WarrantyInfo

    schema = ExtractedProduct(
        brand="Mondial",
        model_code="L-900",
        name="Liquidificador Turbo Power",
        description="Potente e versátil.\nIdeal para o dia a dia.",
        model_variants=["L-900", "L-1000", "L-1200"],
        voltage="127V",
        power_w=900,
        specs={"jar_material": "Vidro", "speeds": 12},
        safety_warnings=["Não ligue vazio", "Desligue da tomada ao limpar"],
        key_usage_steps=["Encaixe o copo", "Selecione a velocidade"],
        installation_requirements=["Superfície plana e seca"],
        warranty=WarrantyInfo(legal_days=90, additional_days=275, total_days=365),
        confidence=0.5,
        low_confidence_fields=["model_code"],
    )
    dump = schema.model_dump(mode="json")
    extra = _specs_extra_lines(dump)
    assert "model_variants=" in extra
    assert "L-1000" in extra
    assert "warranty_total_days=365" in extra
    assert "warranty.total_days=" not in extra
    assert "safety_warnings=" in extra
    assert "key_usage_steps=" in extra
    assert "jar_material=Vidro" in extra

    sections = build_proposal_sections(schema)
    assert len(sections["model_variants"]) >= 2
    assert sections["warranty"]
    assert sections["safety_warnings"]
    assert sections["key_usage_steps"]
    assert any("Material do copo" in c for c in sections["characteristics"])
    assert any("Vidro" in c for c in sections["characteristics"])
    assert any("Garantia legal" in w for w in sections["warranty"])

    sug = build_form_suggestions(schema)
    assert "warranty_total_days=365" in sug["specs_extra"]
    assert "safety_warnings=" in sug["specs_extra"]
    assert "warranty.total_days=" not in sug["specs_extra"]
    assert "warranty_legal_days=90" in sug["specs_extra"]
    options = collect_model_options(schema, brand_name="Mondial")
    assert len(options) >= 2
    codes = {o["code"] for o in options}
    assert "L-900" in codes
    assert "L-1000" in codes
    assert all(o["equipment_model_id"] for o in options)


@pytest.mark.django_db
def test_potencia_in_specs_promoted_to_power_w():
    from apps.dashboard.services.product_ai_assist import (
        build_form_suggestions,
        build_proposal_sections,
    )
    from apps.manuals.schemas import ExtractedProduct

    schema = ExtractedProduct(
        brand="Mondial",
        model_code="MX-400",
        name="Mixer 400W",
        description="Potente.\nCompacto.",
        voltage="127V",
        power_w=None,
        specs={"color": "Preto", "material": "Plástico", "Potencia": "400W"},
        confidence=0.6,
    )
    sections = build_proposal_sections(schema)
    chars = sections["characteristics"]
    assert not any("Potencia" in c or "Potência" in c for c in chars)
    assert not any("400" in c for c in chars)
    assert any("Preto" in c for c in chars)
    assert any("Plástico" in c for c in chars)

    sug = build_form_suggestions(schema)
    assert sug["power_w"] == 400
    assert "potencia=" not in (sug["specs_extra"] or "").casefold()
    assert "power_w=" not in (sug["specs_extra"] or "")


def test_proposal_sections_includes_components():
    from apps.dashboard.services.product_ai_assist import build_proposal_sections
    from apps.manuals.schemas import ComponentHint, ExtractedProduct

    schema = ExtractedProduct(
        brand="Philco",
        model_code="PH800",
        name="Liquidificador Philco",
        description="Linha 1\nLinha 2",
        components=[
            ComponentHint(number="01", name="Tampa"),
            ComponentHint(number="02", name="Copo"),
            ComponentHint(number="", name="Base"),
        ],
    )
    sections = build_proposal_sections(schema)
    assert sections["components"] == ["01 — Tampa", "02 — Copo", "Base"]


def test_recompute_extraction_confidence_multi_model_and_solid():
    from apps.manuals.schemas import ExtractedProduct, WarrantyInfo
    from apps.manuals.services.structure import recompute_extraction_confidence

    multi = ExtractedProduct(
        brand="Mondial",
        model_code="L-900",
        name="Liquidificador Turbo Power",
        description="Linha 1\nLinha 2",
        model_variants=["L-900", "L-1000", "L-1200"],
        voltage="127V",
        power_w=900,
        specs={"speeds": 12},
        safety_warnings=["Não ligue vazio"],
        warranty=WarrantyInfo(total_days=365),
        confidence=0.5,
        low_confidence_fields=[],
    )
    multi = recompute_extraction_confidence(multi)
    assert "model_code" in multi.low_confidence_fields
    assert multi.confidence <= 0.72
    assert multi.confidence > 0.5

    single = ExtractedProduct(
        brand="Mondial",
        model_code="VTE-02",
        name="Ventilador de teto",
        description="Silencioso e eficiente.\nIdeal para salas.",
        voltage="Bivolt",
        power_w=120,
        specs={"blade_count": 3},
        confidence=0.5,
        low_confidence_fields=["model_code"],
    )
    single = recompute_extraction_confidence(single)
    assert "model_code" not in single.low_confidence_fields
    assert single.confidence >= 0.7
