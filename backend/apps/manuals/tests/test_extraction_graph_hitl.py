"""Testes HITL LangGraph na extração (F6 / T-6.2)."""

from __future__ import annotations

import pytest
from django.contrib.auth import get_user_model

from apps.manuals.graphs.extraction import (
    run_extraction_graph,
    thread_id_for,
)
from apps.manuals.models import ExtractionLog
from apps.manuals.services.pipeline import approve_extraction, create_manual_from_upload

User = get_user_model()

# Texto longo o bastante para o mock de structure
FIXTURE_TEXT = (
    "Manual Mondial VTE-02\n"
    "Marca: Mondial\nModelo: VTE-02\n"
    "Peças de reposição: capacitor CAP-35, pá PAL-01.\n"
) * 3


@pytest.fixture
def staff_user(db):
    return User.objects.create_user(
        username="reviewer",
        email="rev@example.com",
        password="x",
        is_staff=True,
    )


@pytest.mark.django_db
def test_extraction_graph_pauses_and_resumes(monkeypatch, staff_user):
    def fake_pdf(_content: bytes):
        class R:
            text = FIXTURE_TEXT
            page_count = 1
            ocr_used = False

        return R()

    monkeypatch.setattr(
        "apps.manuals.graphs.extraction.extract_pdf_text",
        fake_pdf,
    )

    # PDF stub
    content = b"%PDF-1.4\n" + b"%" + b"x" * 80 + b"\n%%EOF\n"
    manual, log = create_manual_from_upload(
        content=content,
        filename="vte.pdf",
        user=staff_user,
        manufacturer="Mondial",
        enqueue=False,
    )
    assert manual.pk
    assert log.status == ExtractionLog.Status.PENDING

    # Reset compiled graph to use fresh checkpointer state for this test
    import apps.manuals.graphs.extraction as eg

    eg._COMPILED = None

    result = run_extraction_graph(log.pk)
    result.refresh_from_db()
    assert result.status == ExtractionLog.Status.AWAITING_REVIEW
    assert result.langgraph_interrupted is True
    assert result.langgraph_thread_id == thread_id_for(log.pk)
    assert result.raw_json  # estruturado antes do interrupt

    # Retomada sem reiniciar (approve via grafo)
    product = approve_extraction(result, reviewer=staff_user, notes="ok")
    result.refresh_from_db()
    assert result.status == ExtractionLog.Status.APPROVED
    assert result.langgraph_interrupted is False
    assert product.sku
    assert product.status == product.Status.DRAFT
