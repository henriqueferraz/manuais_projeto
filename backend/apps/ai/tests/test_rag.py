"""Testes do chat RAG (F5 / R3)."""

from __future__ import annotations

import json

import pytest
from django.core.files.base import ContentFile
from django.test import Client
from django.urls import reverse

from apps.ai.models import ChatFeedback, ChatMessage, ChatSession
from apps.ai.services.chunking import chunk_manual_text
from apps.ai.services.embeddings import cosine_similarity, embed_query
from apps.ai.services.escalate import register_feedback
from apps.ai.services.retrieval import index_manual, retrieve
from apps.manuals.models import Manual
from apps.products.models import Product
from apps.tickets.models import Ticket

MANUAL_TEXT = """
# Instalação
Página 3
Antes de instalar o ventilador Mondial VTE-02, desligue a energia no disjuntor.
Use parafusos adequados ao tipo de forro.

# Manutenção
Página 12
A cada 6 meses limpe as pás com pano seco.
O capacitor de partida do modelo VTE-02 é de 3.5 uF e fica no compartimento superior.

# Tabela de peças
Página 18
| Código | Peça | Compatível |
| CAP-35 | Capacitor 3.5uF | VTE-02 |
| PAL-01 | Pá plástica | VTE-02 |
"""


@pytest.fixture
def indexed_manual(db):
    product = Product.objects.create(
        sku="VTE-02-TEST",
        brand="Mondial",
        model_code="VTE-02",
        status=Product.Status.PUBLISHED,
        price=199,
    )
    manual = Manual(
        original_filename="vte02.pdf",
        mime_type="application/pdf",
        manufacturer="Mondial",
        linked_product=product,
        scan_status=Manual.ScanStatus.SKIPPED,
    )
    manual.file.save("vte02.pdf", ContentFile(b"%PDF-1.4\n%%EOF\n"), save=False)
    manual.compute_and_set_sha256(b"%PDF-1.4\n%%EOF\n")
    manual.save()
    count = index_manual(manual.pk, text=MANUAL_TEXT)
    assert count >= 2
    return manual


def test_chunking_preserves_table_and_sections():
    chunks = chunk_manual_text(MANUAL_TEXT)
    assert chunks
    assert any("capacitor" in c.content.lower() for c in chunks)
    assert any(c.metadata.get("has_table") for c in chunks)
    assert any(c.section for c in chunks)


@pytest.mark.django_db
def test_retrieve_finds_capacitor_chunk(indexed_manual):
    hits = retrieve(
        "Qual o capacitor de partida do VTE-02?",
        product_id=indexed_manual.linked_product_id,
    )
    assert hits, "esperado ao menos um chunk relevante"
    joined = " ".join(h.chunk.content.lower() for h in hits)
    assert "capacitor" in joined
    assert hits[0].chunk.manual_id == indexed_manual.pk


@pytest.mark.django_db
def test_retrieve_filters_by_product(indexed_manual, db):
    other = Product.objects.create(
        sku="OTHER-1",
        brand="Outra",
        model_code="X",
        status=Product.Status.PUBLISHED,
        price=10,
    )
    hits = retrieve("capacitor de partida", product_id=other.pk)
    assert hits == []


@pytest.mark.django_db
def test_chat_page_ok(client: Client):
    response = client.get(reverse("ai:chat"))
    assert response.status_code == 200
    assert b"Assistente de diagn" in response.content or b"diagn" in response.content.lower()
    assert b"tp-chat" in response.content


@pytest.mark.django_db
def test_chat_page_prefills_q(client: Client):
    response = client.get(reverse("ai:chat"), {"q": "Motor compressor Embraco"})
    assert response.status_code == 200
    assert b"Motor compressor Embraco" in response.content


@pytest.mark.django_db
def test_chat_stream_sse(indexed_manual, client: Client):
    url = reverse("ai:chat_stream")
    response = client.post(
        url,
        data=json.dumps(
            {
                "question": "Qual o capacitor de partida do VTE-02?",
                "product_id": indexed_manual.linked_product_id,
            }
        ),
        content_type="application/json",
    )
    assert response.status_code == 200
    assert "text/event-stream" in response["Content-Type"]
    body = b"".join(response.streaming_content).decode("utf-8")
    assert "event: meta" in body
    assert "event: token" in body
    assert "event: done" in body
    assert ChatMessage.objects.filter(role=ChatMessage.Role.ASSISTANT).exists()
    assistant = ChatMessage.objects.filter(role=ChatMessage.Role.ASSISTANT).latest("created_at")
    assert assistant.found_in_manual is True
    assert assistant.sources
    assert "capacitor" in assistant.content.lower() or "fonte" in assistant.content.lower()


@pytest.mark.django_db
def test_chat_fallback_when_no_chunks(db, client: Client):
    response = client.post(
        reverse("ai:chat_stream"),
        data=json.dumps({"question": "procedimento inexistente xyzzy-123"}),
        content_type="application/json",
    )
    body = b"".join(response.streaming_content).decode("utf-8")
    assert "não encontrei" in body.lower() or "nao encontrei" in body.lower()


@pytest.mark.django_db
def test_feedback_down_twice_opens_ticket(indexed_manual, client: Client):
    session = ChatSession.objects.create(
        anonymous_key="anon-test",
        product=indexed_manual.linked_product,
    )
    client.session["tp_chat_key"] = "anon-test"
    client.session.save()

    m1 = ChatMessage.objects.create(
        session=session,
        role=ChatMessage.Role.ASSISTANT,
        content="resposta 1",
        found_in_manual=True,
        confidence=0.8,
        chunk_ids=[],
    )
    ChatMessage.objects.create(
        session=session,
        role=ChatMessage.Role.USER,
        content="pergunta",
    )
    m2 = ChatMessage.objects.create(
        session=session,
        role=ChatMessage.Role.ASSISTANT,
        content="resposta 2",
        found_in_manual=True,
        confidence=0.8,
        chunk_ids=[],
    )

    # força sessão no client
    session_store = client.session
    session_store["tp_chat_key"] = "anon-test"
    session_store.save()

    r1 = client.post(
        reverse("ai:chat_feedback"),
        data=json.dumps({"message_id": str(m1.pk), "vote": "down"}),
        content_type="application/json",
    )
    assert r1.status_code == 200
    assert r1.json()["ticket_code"] is None

    r2 = client.post(
        reverse("ai:chat_feedback"),
        data=json.dumps({"message_id": str(m2.pk), "vote": "down", "email": "cli@ex.com"}),
        content_type="application/json",
    )
    assert r2.status_code == 200
    assert r2.json()["ticket_code"]
    ticket = Ticket.objects.get(code=r2.json()["ticket_code"])
    assert ticket.origin == Ticket.Origin.CHAT
    assert "Histórico" in ticket.description or "histórico" in ticket.description.lower()


@pytest.mark.django_db
def test_feedback_up_persists(indexed_manual):
    session = ChatSession.objects.create(anonymous_key="x")
    msg = ChatMessage.objects.create(
        session=session,
        role=ChatMessage.Role.ASSISTANT,
        content="ok",
        chunk_ids=[1, 2],
    )
    fb = register_feedback(msg, vote=ChatFeedback.Vote.UP, reason="boa")
    assert fb.vote == ChatFeedback.Vote.UP
    assert fb.chunk_ids_snapshot == [1, 2]


@pytest.mark.django_db
def test_retrieve_falls_back_when_pgvector_vecs_null(indexed_manual, settings, monkeypatch):
    """Regressão beta S-001: embedding_vec NULL não pode engolir o JSON hybrid."""
    settings.USE_PGVECTOR = True
    from apps.ai.services import retrieval as retrieval_mod

    class _Conn:
        vendor = "postgresql"

    monkeypatch.setattr(retrieval_mod, "connection", _Conn())
    monkeypatch.setattr(retrieval_mod, "_retrieve_pgvector", lambda *a, **k: [])

    hits = retrieve(
        "Qual o capacitor de partida do VTE-02?",
        product_id=indexed_manual.linked_product_id,
    )
    assert hits, "esperado fallback JSON/hybrid com chunks indexados"
    assert any("capacitor" in h.chunk.content.lower() for h in hits)


def test_mock_embedding_stable():
    a = embed_query("capacitor de partida VTE-02")
    b = embed_query("capacitor de partida VTE-02")
    assert a == b
    assert cosine_similarity(a, b) > 0.99
    c = embed_query("receita de bolo de chocolate")
    assert cosine_similarity(a, c) < cosine_similarity(a, b)
