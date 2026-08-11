"""Grafo de extração com interrupt HITL (F6 / T-6.2)."""

from __future__ import annotations

from decimal import Decimal
from typing import Any, TypedDict

import structlog
from django.utils import timezone
from langgraph.checkpoint.memory import MemorySaver
from langgraph.graph import END, START, StateGraph
from langgraph.types import Command, interrupt

from apps.manuals.models import ExtractionLog
from apps.manuals.services.pdf_extract import extract_pdf_text
from apps.manuals.services.sanitize import sanitize_manual_text
from apps.manuals.services.structure import dump_product_json, structure_manual_text

logger = structlog.get_logger(__name__)

# Checkpointer em memória (processo). Em Celery eager/CI a retomada funciona
# no mesmo worker; thread_id fica no ExtractionLog para correlacionar.
_CHECKPOINTER = MemorySaver()
_COMPILED = None


class ExtractionGraphState(TypedDict, total=False):
    extraction_id: int
    raw_text_preview: str
    raw_json: dict[str, Any]
    model_name: str
    tokens_in: int
    tokens_out: int
    cost_estimate: str
    confidence: float
    langsmith_trace_id: str
    prompt_version: str
    review_decision: dict[str, Any]
    product_id: int | None
    status: str
    error: str


def thread_id_for(extraction_id: int) -> str:
    return f"extraction-{extraction_id}"


def extract_and_structure_node(state: ExtractionGraphState) -> dict[str, Any]:
    log = ExtractionLog.objects.select_related("manual").get(pk=state["extraction_id"])
    log.mark_running()
    manual = log.manual
    content = manual.file.read()
    if hasattr(manual.file, "seek"):
        manual.file.seek(0)

    pdf = extract_pdf_text(content)
    cleaned = sanitize_manual_text(pdf.text)
    if len(cleaned) < 40:
        from django.conf import settings

        if not getattr(settings, "MANUAL_OCR_ENABLED", False):
            raise ValueError(
                "Texto insuficiente no PDF (provável scan/imagem). "
                "Habilite MANUAL_OCR_ENABLED=true no .env, instale tesseract-ocr "
                "(e o idioma português) e tente de novo — ou envie um PDF com texto selecionável."
            )
        raise ValueError(
            "Texto insuficiente mesmo após OCR. "
            "Verifique se o Tesseract está instalado (tesseract-ocr + tesseract-ocr-por), "
            "se a qualidade do scan permite leitura, ou envie um PDF com texto selecionável."
        )

    result = structure_manual_text(
        cleaned,
        manufacturer_hint=manual.manufacturer,
        filename=manual.original_filename,
    )
    product_data = dump_product_json(result.product)
    return {
        "raw_text_preview": cleaned[:4000],
        "raw_json": product_data,
        "model_name": result.model_name,
        "tokens_in": result.tokens_in,
        "tokens_out": result.tokens_out,
        "cost_estimate": str(result.cost_estimate),
        "confidence": result.product.confidence,
        "langsmith_trace_id": result.langsmith_trace_id,
        "prompt_version": result.prompt_version,
        "status": ExtractionLog.Status.AWAITING_REVIEW,
    }


def persist_awaiting_node(state: ExtractionGraphState) -> dict[str, Any]:
    log = ExtractionLog.objects.select_related("manual").get(pk=state["extraction_id"])
    log.raw_text_preview = state.get("raw_text_preview") or ""
    log.raw_json = state.get("raw_json") or {}
    log.model_name = state.get("model_name") or ""
    log.tokens_in = int(state.get("tokens_in") or 0)
    log.tokens_out = int(state.get("tokens_out") or 0)
    log.cost_estimate = Decimal(str(state.get("cost_estimate") or "0"))
    log.confidence = state.get("confidence")
    log.langsmith_trace_id = state.get("langsmith_trace_id") or ""
    log.prompt_version = state.get("prompt_version") or log.prompt_version
    log.status = ExtractionLog.Status.AWAITING_REVIEW
    log.finished_at = timezone.now()
    log.error_message = ""
    log.langgraph_thread_id = thread_id_for(log.pk)
    log.langgraph_interrupted = True
    log.save()

    manufacturer = (state.get("raw_json") or {}).get("manufacturer") or ""
    if not log.manual.manufacturer and manufacturer:
        log.manual.manufacturer = manufacturer
        log.manual.save(update_fields=["manufacturer", "updated_at"])

    logger.info(
        "extraction_graph_awaiting_review",
        extraction_id=log.pk,
        thread_id=log.langgraph_thread_id,
    )
    return {"status": ExtractionLog.Status.AWAITING_REVIEW}


def human_review_node(state: ExtractionGraphState) -> dict[str, Any]:
    """Pausa o grafo até aprovação/rejeição na tela de revisão."""
    decision = interrupt(
        {
            "extraction_id": state["extraction_id"],
            "message": "Aguardando revisão humana (HITL)",
            "draft_keys": list((state.get("raw_json") or {}).keys()),
        }
    )
    return {"review_decision": decision or {}}


def finalize_node(state: ExtractionGraphState) -> dict[str, Any]:
    from apps.manuals.services.pipeline import apply_review_decision

    decision = state.get("review_decision") or {}
    action = decision.get("action") or "approve"
    log = ExtractionLog.objects.get(pk=state["extraction_id"])
    result = apply_review_decision(
        log,
        action=action,
        reviewer_id=decision.get("reviewer_id"),
        corrected=decision.get("corrected"),
        notes=decision.get("notes") or "",
    )
    log.refresh_from_db()
    log.langgraph_interrupted = False
    log.save(update_fields=["langgraph_interrupted", "updated_at"])
    product_id = None
    if action != "reject" and hasattr(result, "pk"):
        # approve returns Product
        from apps.products.models import Product

        if isinstance(result, Product):
            product_id = result.pk
    return {
        "status": log.status,
        "product_id": product_id,
    }


def build_extraction_graph():
    graph = StateGraph(ExtractionGraphState)
    graph.add_node("extract_structure", extract_and_structure_node)
    graph.add_node("persist_awaiting", persist_awaiting_node)
    graph.add_node("human_review", human_review_node)
    graph.add_node("finalize", finalize_node)

    graph.add_edge(START, "extract_structure")
    graph.add_edge("extract_structure", "persist_awaiting")
    graph.add_edge("persist_awaiting", "human_review")
    graph.add_edge("human_review", "finalize")
    graph.add_edge("finalize", END)
    return graph.compile(checkpointer=_CHECKPOINTER)


def get_extraction_graph():
    global _COMPILED
    if _COMPILED is None:
        _COMPILED = build_extraction_graph()
    return _COMPILED


def run_extraction_graph(extraction_id: int) -> ExtractionLog:
    """Inicia o grafo e pausa no interrupt HITL."""
    graph = get_extraction_graph()
    config = {"configurable": {"thread_id": thread_id_for(extraction_id)}}
    try:
        graph.invoke({"extraction_id": extraction_id}, config=config)
    except Exception as exc:  # noqa: BLE001
        # interrupt() em algumas versões não levanta; se falhar de verdade, marca failed
        log = ExtractionLog.objects.filter(pk=extraction_id).first()
        if log and log.status == ExtractionLog.Status.RUNNING:
            logger.exception("extraction_graph_failed", extraction_id=extraction_id)
            log.mark_failed(str(exc))
            return log
        # Pode ser GraphInterrupt — estado já persistido em awaiting_review
        raise
    return ExtractionLog.objects.get(pk=extraction_id)


def resume_extraction_graph(
    extraction_id: int,
    *,
    action: str,
    reviewer_id: int | None,
    corrected: dict | None = None,
    notes: str = "",
) -> ExtractionLog:
    """Retoma o grafo a partir do interrupt (não reinicia extract/structure)."""
    graph = get_extraction_graph()
    config = {"configurable": {"thread_id": thread_id_for(extraction_id)}}
    payload = {
        "action": action,
        "reviewer_id": reviewer_id,
        "corrected": corrected,
        "notes": notes,
    }
    graph.invoke(Command(resume=payload), config=config)
    return ExtractionLog.objects.get(pk=extraction_id)
