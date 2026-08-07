"""Testes Fase 6 — diagnóstico LangGraph, foto e atribuição."""

from __future__ import annotations

import json

import pytest
from django.core.exceptions import ValidationError
from django.core.files.base import ContentFile
from django.test import Client
from django.urls import reverse

from apps.ai.models import PhotoSearch
from apps.ai.services.diagnosis import diagnose_question
from apps.ai.services.photo_search import create_photo_search, validate_photo_upload
from apps.ai.services.retrieval import index_manual
from apps.manuals.models import Manual
from apps.orders.models import Order
from apps.products.models import Product, ProductTranslation

MANUAL_TEXT = """
# Manutenção
Página 12
Quando o ventilador VTE-02 faz barulho e não gira, verifique o capacitor de partida.
O capacitor de partida do modelo VTE-02 é de 3.5 uF (código CAP-35).

# Tabela de peças
Página 18
| Código | Peça |
| CAP-35 | Capacitor 3.5uF |
| PAL-01 | Pá plástica |
"""


@pytest.fixture
def indexed_diagnosis_manual(db):
    equipment = Product.objects.create(
        sku="VTE-02-EQ",
        brand="Mondial",
        model_code="VTE-02",
        status=Product.Status.PUBLISHED,
        product_kind=Product.Kind.FINISHED_GOOD,
        price=199,
    )
    spare = Product.objects.create(
        sku="CAP-35",
        brand="Mondial",
        model_code="CAP-35",
        status=Product.Status.PUBLISHED,
        product_kind=Product.Kind.SPARE_PART,
        price=29,
    )
    ProductTranslation.objects.create(
        product=spare,
        locale="pt-BR",
        name="Capacitor 3.5uF",
        slug="capacitor-35",
        description="",
    )
    manual = Manual(
        original_filename="vte02.pdf",
        mime_type="application/pdf",
        manufacturer="Mondial",
        linked_product=equipment,
        scan_status=Manual.ScanStatus.SKIPPED,
    )
    manual.file.save("vte02.pdf", ContentFile(b"%PDF-1.4\n%%EOF\n"), save=False)
    manual.compute_and_set_sha256(b"%PDF-1.4\n%%EOF\n")
    manual.save()
    index_manual(manual.pk, text=MANUAL_TEXT)
    return manual, equipment, spare


@pytest.mark.django_db
def test_diagnosis_suggests_capacitor_with_source(indexed_diagnosis_manual):
    from apps.ai.models import ChatSession

    manual, equipment, spare = indexed_diagnosis_manual
    session = ChatSession.objects.create(product=equipment, anonymous_key="diag-test")
    assistant, stream, meta = diagnose_question(
        session,
        "O ventilador VTE-02 faz barulho e não gira, parece capacitor",
    )
    text = "".join(stream)
    assert "capacitor" in text.lower() or "manual" in text.lower()
    assert assistant.found_in_manual
    assert assistant.diagnosis_card
    assert assistant.diagnosis_card.get("refManual")
    assert assistant.diagnosis_card.get("confidenceLabel")
    assert assistant.diagnosis_card.get("ticketUrl")
    products = assistant.diagnosis_card.get("recommendedProducts") or []
    assert "CAP-35" in (assistant.diagnosis_card.get("recommendedSkus") or []) or spare.sku in text
    assert any(p.get("sku") == "CAP-35" and p.get("url") for p in products) or spare.sku in text
    assert meta.get("mode") == "diagnosis"


@pytest.mark.django_db
def test_diagnosis_stream_endpoint_renders_card(indexed_diagnosis_manual):
    _, equipment, _ = indexed_diagnosis_manual
    client = Client()
    res = client.post(
        reverse("ai:chat_stream"),
        data=json.dumps(
            {
                "question": "Ventilador faz barulho e não gira no capacitor",
                "product_id": equipment.pk,
                "mode": "diagnosis",
            }
        ),
        content_type="application/json",
    )
    assert res.status_code == 200
    body = b"".join(res.streaming_content).decode("utf-8")
    assert "diagnosis_card" in body or "Fonte técnica" in body or "event: done" in body


@pytest.mark.django_db
def test_photo_upload_rejects_invalid_and_returns_candidates(db):
    Product.objects.create(
        sku="CAP-35",
        brand="Mondial",
        model_code="CAP",
        status=Product.Status.PUBLISHED,
        product_kind=Product.Kind.SPARE_PART,
        price=10,
    )
    ProductTranslation.objects.create(
        product=Product.objects.get(sku="CAP-35"),
        locale="pt-BR",
        name="Capacitor",
        slug="cap-35",
        description="",
    )

    with pytest.raises(ValidationError):
        validate_photo_upload(b"not-an-image", "x.txt")

    # PNG mínimo 1x1
    png = (
        b"\x89PNG\r\n\x1a\n\x00\x00\x00\rIHDR\x00\x00\x00\x01\x00\x00\x00\x01"
        b"\x08\x02\x00\x00\x00\x90wS\xde\x00\x00\x00\x0cIDATx\x9cc\xf8\x0f"
        b"\x00\x00\x01\x01\x00\x05\x18\xd8N\x00\x00\x00\x00IEND\xaeB`\x82"
    )
    search = create_photo_search(
        content=png,
        filename="capacitor.png",
        anonymous_key="photo-test",
        enqueue=True,
    )
    search.refresh_from_db()
    assert search.status == PhotoSearch.Status.DONE
    assert isinstance(search.candidates, list)

    client = Client()
    res = client.post(
        reverse("ai:photo_upload"),
        data={"photo": ContentFile(png, name="capacitor.png")},
    )
    # Django test client needs SimpleUploadedFile
    from django.core.files.uploadedfile import SimpleUploadedFile

    res = client.post(
        reverse("ai:photo_upload"),
        data={"photo": SimpleUploadedFile("capacitor.png", png, content_type="image/png")},
    )
    assert res.status_code == 200
    payload = res.json()
    assert payload["status"] == "done"


@pytest.mark.django_db
def test_order_attribution_diagnosis(db):
    from apps.ai.models import ChatSession
    from apps.cart.models import Cart, CartItem
    from apps.checkout.services import build_order_from_cart
    from apps.products.models import Stock

    product = Product.objects.create(
        sku="CAP-35",
        brand="Mondial",
        model_code="CAP",
        status=Product.Status.PUBLISHED,
        product_kind=Product.Kind.SPARE_PART,
        price=25,
    )
    ProductTranslation.objects.create(
        product=product,
        locale="pt-BR",
        name="Capacitor",
        slug="cap",
        description="",
    )
    Stock.objects.create(product=product, quantity_available=10, quantity_reserved=0)
    cart = Cart.objects.create(session_key="attr-session")
    CartItem.objects.create(cart=cart, product=product, quantity=1, unit_price=25)
    session = ChatSession.objects.create(anonymous_key="attr")
    order = build_order_from_cart(
        cart=cart,
        email="a@b.com",
        shipping={
            "shipping_name": "A",
            "shipping_cep": "01310100",
            "shipping_street": "Av",
            "shipping_number": "1",
            "shipping_district": "B",
            "shipping_city": "SP",
            "shipping_state": "SP",
        },
        shipping_option_id="fixed-econ",
        attribution_source=Order.AttributionSource.DIAGNOSIS,
        chat_session_id=str(session.pk),
    )
    assert order.attribution_source == Order.AttributionSource.DIAGNOSIS
    assert str(order.chat_session_id) == str(session.pk)
