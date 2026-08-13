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
from apps.ai.services.confidence import (
    format_low_confidence_message,
    is_below_answer_threshold,
    min_answer_confidence,
)
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
    """Carrega o system prompt de diagnóstico; fallback embutido se faltar arquivo."""
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

    from apps.ai.services.product_context import compose_diagnosis_symptom

    # Junta sintoma anterior com resposta de tipo/modelo ("cafeteira") antes de buscar.
    composed = compose_diagnosis_symptom(session, cleaned)
    locale = detect_text_locale(composed)
    graph_symptom = composed
    if locale != "pt-BR":
        graph_symptom = f"[Respond in locale={locale}]\n{composed}"

    ChatMessage.objects.create(
        session=session,
        role=ChatMessage.Role.USER,
        content=cleaned,
    )
    if not session.title:
        session.title = f"Diagnóstico: {composed[:100]}"
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

    # Persiste tipo/modelo resolvido do texto para as próximas mensagens da sessão.
    session_updates: list[str] = []
    resolved_product_id = result.get("product_id")
    resolved_category_id = result.get("category_id")
    if resolved_product_id and not session.product_id:
        session.product_id = int(resolved_product_id)
        session_updates.append("product_id")
    if resolved_category_id and not session.category_id:
        session.category_id = int(resolved_category_id)
        session_updates.append("category_id")
    if session_updates:
        session_updates.append("updated_at")
        session.save(update_fields=session_updates)

    answer = (result.get("answer") or FALLBACK_MSG).strip()
    sources = result.get("sources") or []
    confidence = float(result.get("confidence") or 0.0)
    found = bool(result.get("found_in_manual"))
    decision = result.get("decision") or ""
    # Pedido de tipo/modelo ou mais detalhes — não abre chamado automático.
    skip_confidence_gate = decision in {"ask_details", "ask_product"}
    skus = result.get("recommended_skus") or []
    products = _sku_product_links(skus)
    from django.urls import reverse

    ticket_url = reverse("tickets:list")
    ticket_code = None

    tokens_in = max(1, len(composed) // 4)
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
        diagnosis_card={},
    )
    assistant.save()

    if not skip_confidence_gate and is_below_answer_threshold(confidence):
        from apps.ai.services.escalate import escalate_session

        threshold = min_answer_confidence()
        found = False
        assistant.found_in_manual = False
        assistant.save(update_fields=["found_in_manual"])
        ticket = escalate_session(
            session,
            trigger_message=assistant,
            reason=(
                f"Confiança do diagnóstico ({confidence:.0%}) abaixo do mínimo "
                f"({threshold:.0%}); agente recusou inventar resposta."
            ),
            email=getattr(session.user, "email", "") if session.user_id else "",
            user=session.user if session.user_id else None,
        )
        ticket_code = ticket.code
        answer = format_low_confidence_message(ticket_code)
        sources = []
        skus = []
        products = []
        tokens_out = max(1, len(answer) // 4)
        assistant.sources = []
        assistant.chunk_ids = []
        assistant.tokens_out = tokens_out
        assistant.cost_estimate = _estimate_cost(tokens_in, tokens_out)
        assistant.model_name = "low-confidence-fallback"
        assistant.save(
            update_fields=[
                "sources",
                "chunk_ids",
                "tokens_out",
                "cost_estimate",
                "model_name",
            ]
        )
        logger.info(
            "diagnosis_low_confidence_refused",
            session_id=str(session.pk),
            message_id=str(assistant.pk),
            confidence=confidence,
            threshold=threshold,
            ticket_code=ticket_code,
        )

    card = None
    if skip_confidence_gate:
        card = {
            "title": (
                "Qual é o produto?" if decision == "ask_product" else "Preciso de mais detalhes"
            ),
            "confidence": None,
            "confidenceLabel": "",
            "description": answer[:500],
            "refManual": "",
            "recommendedSkus": [],
            "recommendedProducts": [],
            "ticketUrl": ticket_url,
            "ticketLabel": "Abrir chamado para atendimento humano",
            "fallback": True,
        }
    elif found and result.get("ref_manual") and not ticket_code:
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
    else:
        card = {
            "title": "Sem evidência suficiente",
            "confidence": confidence,
            "confidenceLabel": f"{int(round(confidence * 100))}%",
            "description": answer[:500],
            "refManual": "",
            "recommendedSkus": [],
            "recommendedProducts": [],
            "ticketUrl": ticket_url,
            "ticketLabel": (
                f"Chamado {ticket_code} aberto"
                if ticket_code
                else "Abrir chamado para atendimento humano"
            ),
            "ticketCode": ticket_code,
            "fallback": True,
        }

    assistant.diagnosis_card = card or {}
    assistant.save(update_fields=["diagnosis_card"])
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
                confidence=confidence,
                ticket_code=ticket_code,
                skus=skus,
                latency_ms=latency_ms,
            )
            cost_alert = float(getattr(settings, "AI_COST_ALERT_USD", 5.0))
            if float(assistant.cost_estimate) >= cost_alert:
                logger.warning("ai_cost_alert", cost=float(assistant.cost_estimate))

    meta = {
        "mode": "diagnosis",
        "diagnosis_card": card,
        "recommended_skus": skus,
        "decision": decision,
        "locale": locale,
        "model_name": assistant.model_name,
        "ticket_code": ticket_code,
    }
    return assistant, stream(), meta


def attribution_payload(*, source: str, session: ChatSession | None) -> dict:
    """Campos para gravar em Order a partir do diagnóstico/chat/foto."""
    return {
        "attribution_source": source,
        "chat_session_id": str(session.pk) if session else None,
    }
