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
    assert assistant.confidence is not None and assistant.confidence >= 0.70
    assert assistant.diagnosis_card
    assert assistant.diagnosis_card.get("refManual")
    assert assistant.diagnosis_card.get("confidenceLabel")
    assert assistant.diagnosis_card.get("ticketUrl")
    products = assistant.diagnosis_card.get("recommendedProducts") or []
    assert "CAP-35" in (assistant.diagnosis_card.get("recommendedSkus") or []) or spare.sku in text
    assert any(p.get("sku") == "CAP-35" and p.get("url") for p in products) or spare.sku in text
    assert meta.get("mode") == "diagnosis"
    assert meta.get("ticket_code") is None
    assert assistant.model_name == "langgraph-diagnosis-mock"


@pytest.mark.django_db
def test_diagnosis_ask_details_does_not_auto_ticket(db):
    from apps.ai.models import ChatSession

    session = ChatSession.objects.create(anonymous_key="ask-details")
    assistant, stream, meta = diagnose_question(session, "ajuda")
    text = "".join(stream)
    low = text.lower()
    assert "tipo de produto" in low or "modelo" in low
    assert meta.get("decision") == "ask_product"
    assert meta.get("ticket_code") is None
    session.refresh_from_db()
    assert session.escalated_ticket_id is None
    assert assistant.confidence is not None and assistant.confidence < 0.70


@pytest.mark.django_db
def test_diagnosis_asks_product_type_before_search(db):
    """Sem tipo/modelo, não busca no manual — pergunta ao cliente primeiro."""
    from apps.ai.graphs.diagnosis import run_diagnosis
    from apps.ai.models import ChatSession

    session = ChatSession.objects.create(anonymous_key="ask-type")
    assistant, stream, meta = diagnose_question(
        session,
        "faz barulho e não gira desde ontem",
    )
    text = "".join(stream).lower()
    assert "tipo de produto" in text or "modelo" in text
    assert meta.get("decision") == "ask_product"
    assert meta.get("ticket_code") is None
    assert assistant.found_in_manual is False

    result = run_diagnosis(symptom="faz barulho e não gira desde ontem")
    assert result.get("decision") == "ask_product"
    assert not result.get("chunks")


@pytest.mark.django_db
def test_diagnosis_uses_product_type_from_text(db):
    """Com tipo no relato, restringe busca e segue o fluxo (não pede tipo de novo)."""
    from apps.ai.graphs.diagnosis import run_diagnosis
    from apps.ai.services.product_context import resolve_product_context
    from apps.catalog.models import Category

    cat = Category.objects.create(name="Liquidificadores", slug="liquidificadores")
    ctx = resolve_product_context("meu liquidificador não liga")
    assert ctx.has_context
    assert ctx.category_id == cat.pk
    assert ctx.source == "text_type"

    result = run_diagnosis(symptom="meu liquidificador não liga")
    assert result.get("decision") != "ask_product"
    assert result.get("category_id") == cat.pk


@pytest.mark.django_db
def test_diagnosis_merges_type_followup_with_prior_symptom(db):
    """
    Regressão: 'não liga' → pergunta tipo → 'cafeteira' não pode virar
    resposta genérica da capa do manual (MODELO / UTILIZANDO).
    """
    from apps.ai.models import ChatMessage, ChatSession
    from apps.ai.services.product_context import (
        compose_diagnosis_symptom,
        session_continues_diagnosis,
    )
    from apps.ai.views import _wants_diagnosis
    from apps.catalog.models import Category

    Category.objects.create(name="Cafeteiras", slug="cafeteiras")
    session = ChatSession.objects.create(anonymous_key="cafeteira-followup")

    assistant1, stream1, meta1 = diagnose_question(session, "o produto não liga")
    assert meta1.get("decision") == "ask_product"
    "".join(stream1)
    assert assistant1.diagnosis_card.get("title") == "Qual é o produto?"
    assert not assistant1.diagnosis_card.get("confidenceLabel")

    # Antes da 2ª mensagem: o turno atual ainda não foi gravado.
    assert session_continues_diagnosis(session, "cafeteira")
    assert _wants_diagnosis("cafeteira", None, session=session)
    composed = compose_diagnosis_symptom(session, "cafeteira")
    assert "não liga" in composed.lower() or "nao liga" in composed.lower()
    assert "cafeteira" in composed.lower()

    cat = Category.objects.get(slug="cafeteiras")
    equipment = Product.objects.create(
        sku="CAF-01",
        brand="Genérico",
        model_code="CAF-01",
        category=cat,
        status=Product.Status.PUBLISHED,
        product_kind=Product.Kind.FINISHED_GOOD,
        price=149,
    )
    manual = Manual(
        original_filename="cafeteira.pdf",
        mime_type="application/pdf",
        manufacturer="Genérico",
        linked_product=equipment,
        scan_status=Manual.ScanStatus.SKIPPED,
    )
    manual.file.save("cafeteira.pdf", ContentFile(b"%PDF-1.4\n%%EOF\n"), save=False)
    manual.compute_and_set_sha256(b"%PDF-1.4\n%%EOF\n")
    manual.save()
    index_manual(
        manual.pk,
        text=(
            "# MODELO\n"
            "Página 1\n"
            "Manual de Instruções Cafeteira Elétrica\n\n"
            "# UTILIZANDO SEU PRODUTO\n"
            "Página 3\n"
            "Coloque água no reservatório e ligue o produto.\n\n"
            "# LIMPEZA E CONSERVAÇÃO\n"
            "Página 8\n"
            "Limpe a cafeteira com pano úmido.\n"
        ),
    )

    assistant2, stream2, meta2 = diagnose_question(session, "cafeteira")
    text = "".join(stream2).lower()
    assert meta2.get("decision") != "ask_product"
    assert "modelo manual de instruções" not in text
    assert "utilizando seu produto" not in text
    # Sem evidência de diagnóstico no manual → recusa / chamado, não capa genérica.
    assert (
        "não sei" in text or "nao sei" in text or "não encontrei" in text or "nao encontrei" in text
    )
    assert assistant2.found_in_manual is False
    assert ChatMessage.objects.filter(session=session, role=ChatMessage.Role.USER).count() == 2


@pytest.mark.django_db
def test_diagnosis_low_confidence_opens_ticket(indexed_diagnosis_manual):
    from apps.ai.models import ChatSession

    _, equipment, _ = indexed_diagnosis_manual
    session = ChatSession.objects.create(product=equipment, anonymous_key="diag-low")
    # "não liga" ≠ "não gira" do manual — não deve inventar diagnóstico.
    assistant, stream, meta = diagnose_question(
        session,
        "meu equipamento não liga e solta fumaça roxa xyzzy-999",
    )
    text = "".join(stream)
    assert "não sei" in text.lower() or "nao sei" in text.lower() or "não encontrei" in text.lower()
    assert meta.get("ticket_code")
    session.refresh_from_db()
    assert session.escalated_ticket_id is not None
    assert assistant.found_in_manual is False
    assert assistant.confidence is not None and assistant.confidence < 0.70


OSTER_SAFETY_TEXT = """
# INSTRUÇÕES IMPORTANTES DE SEGURANÇA
Página 1
Verifique se a tensão (voltagem) do produto é compatível com a tomada a ser utilizada.
Não ligue o produto em tomadas ou extensões sobrecarregadas.
Antes de ligar o liquidificador certifique-se de que a tampa esteja bem travada.
Se o produto apresentar qualquer defeito, a manutenção deverá ser feita em uma assistência
técnica autorizada Cadence.
MANTENHA ESTAS INSTRUÇÕES

# Usando a Função Triturar Gelo
Página 4
Para usar a função para triturar gelo, gire o botão seletor de velocidades no sentido horário
até a velocidade 8. Coloque o botão na posição O para desligar o liquidificador.
Para triturar gelo: Coloque na Jarra 6 cubos de gelo, aproximadamente 2 xícaras de gelo por vez.

# MOUSSE DE MANGA
Página 7
Ingredientes: 3 Mangas grandes maduras, 1 Envelope de gelatina em pó sem sabor (12g),
1/2 Xícara de água, 200g de Chantily.
Modo de Preparo: Descasque e corte as mangas. Bata no liquidificador utilizando a função pulsar.
Coloque o mousse na forma e leve à geladeira. Sirva com a calda de manga.

# MASSA PARA PIZZA DE LIQUIDIFICADOR
Página 8
Ingredientes: 2 Xícaras de leite, 1/4 de Xícara de óleo, 3 Ovos, farinha de trigo.
Modo de Preparo: Bata no liquidificador os ingredientes líquidos e acrescente os sólidos.
Despeje a massa para pizza em forma untada e asse por 20 minutos.

# MILK SHAKE CREMOSO DE MAMÃO
Página 9
Ingredientes: 2 Xícaras de leite, 2 Mamões papaya, 6 Colheres de leite em pó, 6 Cubos de gelo.
Modo de Preparo: No copo do liquidificador, coloque todos os ingredientes, exceto o gelo.
Bata o milk shake cremoso adicionando o gelo aos poucos. Sirva imediatamente.

# SUCO DE CENOURA COM LARANJA
Página 10
Ingredientes: 2 Cenouras grandes frescas (500 g); 600 ml de água; 1 Laranja; Açúcar a gosto.
Modo de Preparo: Corte as cenouras em pedaços, descasque a laranja e bata no liquidificador.
Adoce a gosto o suco de cenoura com laranja.
"""


@pytest.fixture
def indexed_oster_safety_manual(db):
    """Manual Oster-like: só segurança preventiva, sem diagnóstico de 'não liga'."""
    equipment = Product.objects.create(
        sku="BLSTMG-BR8",
        brand="Oster",
        model_code="BLSTMG-BR8",
        status=Product.Status.PUBLISHED,
        product_kind=Product.Kind.FINISHED_GOOD,
        price=299,
    )
    manual = Manual(
        original_filename="oster.pdf",
        mime_type="application/pdf",
        manufacturer="Oster",
        linked_product=equipment,
        scan_status=Manual.ScanStatus.SKIPPED,
    )
    manual.file.save("oster.pdf", ContentFile(b"%PDF-1.4\n%%EOF\n"), save=False)
    manual.compute_and_set_sha256(b"%PDF-1.4\n%%EOF\n")
    manual.save()
    index_manual(manual.pk, text=OSTER_SAFETY_TEXT)
    return manual, equipment


@pytest.mark.django_db
def test_diagnosis_rejects_preventive_safety_as_wont_turn_on(indexed_oster_safety_manual):
    """Regressão: 'não liga' não pode virar diagnóstico pela trava da tampa."""
    from apps.ai.models import ChatSession
    from apps.ai.services.confidence import evidence_supports_answer

    assert not evidence_supports_answer(
        "meu liquidificador não liga",
        section="INSTRUÇÕES IMPORTANTES DE SEGURANÇA",
        content=(
            "Antes de ligar o liquidificador certifique-se de que a tampa esteja bem travada. "
            "Não ligue o produto em tomadas sobrecarregadas."
        ),
    )

    _, equipment = indexed_oster_safety_manual
    session = ChatSession.objects.create(product=equipment, anonymous_key="oster-noliga")
    assistant, stream, meta = diagnose_question(session, "meu liquidificador não liga")
    text = "".join(stream)
    low = text.lower()
    assert "bem travada" not in low
    assert "não encontrei" in low or "não sei" in low or "nao sei" in low
    assert assistant.found_in_manual is False
    assert (assistant.confidence or 0) < 0.70
    assert meta.get("ticket_code")
    session.refresh_from_db()
    assert session.escalated_ticket_id is not None


def test_evidence_supports_real_fault_chunk():
    from apps.ai.services.confidence import evidence_supports_answer

    assert evidence_supports_answer(
        "O ventilador faz barulho e não gira",
        section="Manutenção",
        content=(
            "Quando o ventilador VTE-02 faz barulho e não gira, "
            "verifique o capacitor de partida."
        ),
    )


@pytest.mark.django_db
def test_diagnosis_answers_usage_and_recipe_from_manual(indexed_oster_safety_manual):
    """Uso/receita devem responder com o trecho — não recusar como 'sem evidência'."""
    from apps.ai.models import ChatSession
    from apps.ai.services.chat import answer_question

    _, equipment = indexed_oster_safety_manual

    session_use = ChatSession.objects.create(product=equipment, anonymous_key="oster-gelo")
    assistant_use, stream_use, meta_use = answer_question(
        session_use,
        "como utilizar a função de triturar gelo?",
    )
    text_use = "".join(stream_use)
    assert assistant_use.found_in_manual is True
    assert assistant_use.confidence is not None and assistant_use.confidence >= 0.70
    assert "gelo" in text_use.lower() or "velocidade" in text_use.lower()
    assert meta_use.get("ticket_code") is None

    session_recipe = ChatSession.objects.create(product=equipment, anonymous_key="oster-mousse")
    assistant_recipe, stream_recipe, meta_recipe = answer_question(
        session_recipe,
        "tem uma receita de MOUSSE DE MANGA?",
    )
    text_recipe = "".join(stream_recipe)
    assert assistant_recipe.found_in_manual is True
    assert assistant_recipe.confidence is not None and assistant_recipe.confidence >= 0.70
    assert "mousse" in text_recipe.lower() or "manga" in text_recipe.lower()
    assert meta_recipe.get("ticket_code") is None


@pytest.mark.django_db
def test_chat_answers_pizza_dough_recipe(indexed_oster_safety_manual):
    from apps.ai.models import ChatSession
    from apps.ai.services.chat import answer_question

    _, equipment = indexed_oster_safety_manual
    session = ChatSession.objects.create(product=equipment, anonymous_key="oster-pizza")
    assistant, stream, meta = answer_question(
        session,
        "tem uma receita de MASSA PARA PIZZA?",
    )
    text = "".join(stream)
    assert assistant.found_in_manual is True
    assert assistant.confidence is not None and assistant.confidence >= 0.70
    assert "massa" in text.lower() or "pizza" in text.lower()
    assert "não sei" not in text.lower()
    assert meta.get("ticket_code") is None


@pytest.mark.django_db
def test_chat_answers_suco_de_cenoura(indexed_oster_safety_manual):
    from apps.ai.models import ChatSession
    from apps.ai.services.chat import answer_question
    from apps.ai.services.chunking import chunk_manual_text

    # Chunker não deve promover linha de ingrediente a título da seção.
    raw = (
        "                        SUCO DE CENOURA COM LARANJA\n"
        "Ingredientes\n"
        "2 Cenouras grandes frescas (500 g);             600 ml de água;\n"
        "1 Laranja;                                      Açúcar a gosto\n\n"
        "Modo de Preparo\n"
        "Corte as cenouras em pedaços e bata com a laranja no liquidificador.\n"
    )
    sections = {c.section for c in chunk_manual_text(raw)}
    assert any("SUCO DE CENOURA" in s for s in sections)
    assert not any(s.strip().startswith("1 Laranja") for s in sections)

    _, equipment = indexed_oster_safety_manual
    session = ChatSession.objects.create(product=equipment, anonymous_key="oster-suco")
    assistant, stream, meta = answer_question(session, "SUCO DE CENOURA")
    text = "".join(stream)
    assert assistant.found_in_manual is True
    assert assistant.confidence is not None and assistant.confidence >= 0.70
    assert "cenoura" in text.lower() or "laranja" in text.lower()
    assert "não sei" not in text.lower()
    assert meta.get("ticket_code") is None


@pytest.mark.django_db
def test_chat_answers_milk_shake_cremoso(indexed_oster_safety_manual):
    from apps.ai.models import ChatSession
    from apps.ai.services.chat import answer_question
    from apps.ai.services.retrieval import retrieve

    _, equipment = indexed_oster_safety_manual
    hits = retrieve("tem receita de MILK SHAKE CREMOSO", product_id=equipment.pk)
    assert hits, "lexical+hybrid deve achar a receita mesmo com embedding fraco"
    assert any("milk" in (h.chunk.content + (h.chunk.section or "")).lower() for h in hits)

    session = ChatSession.objects.create(product=equipment, anonymous_key="oster-shake")
    assistant, stream, meta = answer_question(session, "tem receita de MILK SHAKE CREMOSO")
    text = "".join(stream)
    assert assistant.found_in_manual is True
    assert assistant.confidence is not None and assistant.confidence >= 0.70
    assert "milk" in text.lower() or "shake" in text.lower() or "mamão" in text.lower()
    assert "não sei" not in text.lower()
    assert meta.get("ticket_code") is None


@pytest.mark.django_db
def test_enrich_none_on_usage_keeps_manual_excerpt(
    indexed_oster_safety_manual, settings, monkeypatch
):
    """Se o LLM devolver NO_EVIDENCE em pergunta de uso, ainda assim usamos o trecho."""
    from apps.ai.models import ChatSession

    settings.DIAGNOSIS_LLM_MODE = "openai"
    monkeypatch.setattr(
        "apps.ai.graphs.diagnosis._enrich_diagnosis_openai",
        lambda **kwargs: None,
    )
    _, equipment = indexed_oster_safety_manual
    session = ChatSession.objects.create(product=equipment, anonymous_key="oster-enrich")
    assistant, stream, meta = diagnose_question(
        session,
        "como utilizar a função de triturar gelo?",
    )
    text = "".join(stream)
    assert assistant.found_in_manual is True
    assert "gelo" in text.lower()
    assert meta.get("ticket_code") is None


@pytest.mark.django_db
def test_diagnosis_model_name_openai_when_enriched(indexed_diagnosis_manual, settings, monkeypatch):
    """B-011: com DIAGNOSIS_LLM_MODE=openai e enriquecimento ok, model_name = OPENAI_CHAT_MODEL."""
    from apps.ai.models import ChatSession

    settings.DIAGNOSIS_LLM_MODE = "openai"
    settings.OPENAI_CHAT_MODEL = "gpt-4o-mini"
    monkeypatch.setattr(
        "apps.ai.graphs.diagnosis._enrich_diagnosis_openai",
        lambda **kwargs: "Diagnóstico enriquecido. Fonte: Manutenção, pág. 12. Peças: CAP-35.",
    )
    _, equipment, _ = indexed_diagnosis_manual
    session = ChatSession.objects.create(product=equipment, anonymous_key="diag-b011")
    assistant, stream, meta = diagnose_question(
        session,
        "O ventilador VTE-02 faz barulho e não gira, parece capacitor",
    )
    "".join(stream)
    assert assistant.model_name == "gpt-4o-mini"
    assert meta.get("model_name") == "gpt-4o-mini"


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
