"""Fachada Django ↔ grafo de diagnóstico (F6 / T-6.1)."""

from __future__ import annotations

import time
import uuid
from collections.abc import Iterator
from pathlib import Path

import structlog
from django.conf import settings

from apps.ai.graphs.diagnosis import run_diagnosis
from apps.ai.models import ChatMessage, ChatSession
from apps.ai.services.chat import FALLBACK_MSG, _estimate_cost, _stream_words
from apps.core.i18n import detect_text_locale
from apps.core.ratelimit import record_token_usage
from apps.manuals.services.sanitize import sanitize_manual_text

logger = structlog.get_logger(__name__)

PROMPT_DIR = Path(__file__).resolve().parent.parent / "prompts"


def _sku_product_links(skus: list[str]) -> list[dict]:
    """Resolve SKUs → links de PDP para o card de diagnóstico."""
    from django.urls import reverse

    from apps.products.models import Product

    if not skus:
        return []
    products = {
        p.sku: p
        for p in Product.objects.filter(sku__in=skus, status=Product.Status.PUBLISHED).only(
            "sku", "slug", "brand", "model_code"
        )
    }
    links: list[dict] = []
    for sku in skus:
        product = products.get(sku)
        if product:
            links.append(
                {
                    "sku": sku,
                    "name": f"{product.brand} {product.model_code}".strip() or sku,
                    "url": reverse("catalog:detail", kwargs={"slug": product.slug}),
                }
            )
        else:
            links.append(
                {
                    "sku": sku,
                    "name": sku,
                    "url": f"{reverse('catalog:list')}?q={sku}",
                }
            )
    return links


def load_diagnosis_prompt(version: str = "v2") -> str:
    path = PROMPT_DIR / f"diagnosis_system_{version}.md"
    if path.exists():
        return path.read_text(encoding="utf-8")
    return (
        "Você é o motor de diagnóstico da TechParts AI. "
        "Sempre cite o manual. Sugira SKUs só com evidência. "
        "Não escreva código. Escopo: produto, peça, uso e conserto."
    )


def diagnose_question(
    session: ChatSession,
    question: str,
    *,
    request_id: str = "",
    user_id: int | None = None,
) -> tuple[ChatMessage, Iterator[str], dict]:
    """
    Executa o grafo de diagnóstico, persiste mensagens e devolve stream + card.
    """
    cleaned = sanitize_manual_text(question).strip()
    if not cleaned:
        raise ValueError("Relato vazio.")

    locale = detect_text_locale(cleaned)
    graph_symptom = cleaned
    if locale != "pt-BR":
        graph_symptom = f"[Respond in locale={locale}]\n{cleaned}"

    ChatMessage.objects.create(
        session=session,
        role=ChatMessage.Role.USER,
        content=cleaned,
    )
    if not session.title:
        session.title = f"Diagnóstico: {cleaned[:100]}"
    if request_id:
        session.request_id = request_id
    session.save(update_fields=["title", "request_id", "updated_at"])

    started = time.perf_counter()
    result = run_diagnosis(
        symptom=graph_symptom,
        product_id=session.product_id,
        category_id=session.category_id,
        user_id=user_id,
    )

    answer = (result.get("answer") or FALLBACK_MSG).strip()
    sources = result.get("sources") or []
    confidence = float(result.get("confidence") or 0.0)
    found = bool(result.get("found_in_manual"))
    skus = result.get("recommended_skus") or []
    products = _sku_product_links(skus)
    from django.urls import reverse

    ticket_url = reverse("tickets:list")
    card = None
    if found and result.get("ref_manual"):
        card = {
            "title": result.get("cause") or "Diagnóstico assistido",
            "confidence": confidence,
            "confidenceLabel": f"{int(round(confidence * 100))}%",
            "description": answer[:500],
            "refManual": result["ref_manual"],
            "recommendedSkus": skus,
            "recommendedProducts": products,
            "ticketUrl": ticket_url,
            "ticketLabel": "Abrir chamado com este relato",
        }
    elif not found:
        card = {
            "title": "Sem evidência no manual",
            "confidence": confidence,
            "confidenceLabel": f"{int(round(confidence * 100))}%",
            "description": answer[:500],
            "refManual": "",
            "recommendedSkus": [],
            "recommendedProducts": [],
            "ticketUrl": ticket_url,
            "ticketLabel": "Abrir chamado para atendimento humano",
            "fallback": True,
        }

    tokens_in = max(1, len(cleaned) // 4)
    tokens_out = max(1, len(answer) // 4)
    assistant = ChatMessage(
        session=session,
        role=ChatMessage.Role.ASSISTANT,
        content="",
        sources=sources,
        chunk_ids=[s.get("chunk_id") for s in sources if s.get("chunk_id")],
        confidence=confidence,
        found_in_manual=found,
        tokens_in=tokens_in,
        tokens_out=tokens_out,
        cost_estimate=_estimate_cost(tokens_in, tokens_out),
        model_name=result.get("model_name") or "langgraph-diagnosis-mock",
        langsmith_trace_id=f"diag-{uuid.uuid4().hex[:12]}",
        diagnosis_card=card or {},
    )
    assistant.save()
    record_token_usage(tokens_in + tokens_out)

    def stream() -> Iterator[str]:
        collected: list[str] = []
        try:
            for piece in _stream_words(answer):
                collected.append(piece)
                yield piece
        finally:
            text = "".join(collected) or answer
            latency_ms = int((time.perf_counter() - started) * 1000)
            assistant.content = text
            assistant.latency_ms = latency_ms
            assistant.save(update_fields=["content", "latency_ms"])
            logger.info(
                "diagnosis_done",
                session_id=str(session.pk),
                message_id=str(assistant.pk),
                request_id=request_id,
                found=found,
                skus=result.get("recommended_skus") or [],
                latency_ms=latency_ms,
            )
            cost_alert = float(getattr(settings, "AI_COST_ALERT_USD", 5.0))
            if float(assistant.cost_estimate) >= cost_alert:
                logger.warning("ai_cost_alert", cost=float(assistant.cost_estimate))

    meta = {
        "mode": "diagnosis",
        "diagnosis_card": card,
        "recommended_skus": result.get("recommended_skus") or [],
        "decision": result.get("decision") or "",
        "locale": locale,
        "model_name": assistant.model_name,
    }
    return assistant, stream(), meta


def attribution_payload(*, source: str, session: ChatSession | None) -> dict:
    """Campos para gravar em Order a partir do diagnóstico/chat/foto."""
    return {
        "attribution_source": source,
        "chat_session_id": str(session.pk) if session else None,
    }
