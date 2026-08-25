"""Tools do grafo de diagnóstico: schema, validação e tratamento de falha."""

from __future__ import annotations

import time
from collections.abc import Callable
from typing import Any

import structlog
from django.db import close_old_connections
from django.db.utils import OperationalError
from pydantic import BaseModel, Field, ValidationError

logger = structlog.get_logger(__name__)


def _with_db_retry(fn: Callable[[], Any], *, attempts: int = 6) -> Any:
    """Retry curto se o SQLite estiver locked."""
    last: OperationalError | None = None
    for i in range(attempts):
        close_old_connections()
        try:
            return fn()
        except OperationalError as exc:
            last = exc
            if "locked" not in str(exc).lower():
                raise
            time.sleep(0.04 * (i + 1))
    assert last is not None
    raise last


class RetrieveManualInput(BaseModel):
    """Entrada da tool de busca no manual (RAG)."""

    symptom: str = Field(..., min_length=1, max_length=4000)
    product_id: int | None = None
    category_id: int | None = None
    category_name: str = ""
    model_code: str = ""


class SearchOrdersInput(BaseModel):
    """Entrada da tool de pedidos recentes do usuário."""

    user_id: int | None = None


def retrieve_manual_chunks(payload: dict[str, Any]) -> dict[str, Any]:
    """
    Busca trechos de manual com validação de payload.

    Em falha de schema ou de retrieval, devolve chunks vazios e `error`.
    """
    try:
        args = RetrieveManualInput.model_validate(payload)
    except ValidationError as exc:
        logger.warning("retrieve_manual_invalid_payload", error=str(exc)[:300])
        return {"ok": False, "chunks": [], "error": "payload_invalido", "tool_errors": ["retrieve"]}

    try:
        from apps.ai.services.retrieval import retrieve

        def _run():
            return retrieve(
                args.symptom,
                product_id=args.product_id,
                category_id=args.category_id,
                category_name=args.category_name,
                model_code=args.model_code,
            )

        hits = _with_db_retry(_run)
    except Exception:  # noqa: BLE001
        logger.exception("retrieve_manual_failed")
        return {"ok": False, "chunks": [], "error": "retrieve_failed", "tool_errors": ["retrieve"]}

    chunks = [
        {
            "chunk_id": h.chunk.pk,
            "section": h.chunk.section,
            "page": h.chunk.page,
            "score": round(h.score, 4),
            "manual_id": h.chunk.manual_id,
            "excerpt": h.chunk.content[:240],
            "content": h.chunk.content,
        }
        for h in hits
    ]
    return {"ok": True, "chunks": chunks, "error": "", "tool_errors": []}


def search_user_orders(payload: dict[str, Any]) -> dict[str, Any]:
    """Lista pedidos recentes do usuário; vazio se não autenticado ou em erro."""
    try:
        args = SearchOrdersInput.model_validate(payload)
    except ValidationError as exc:
        logger.warning("search_orders_invalid_payload", error=str(exc)[:300])
        return {
            "ok": False,
            "orders_summary": "",
            "error": "payload_invalido",
            "tool_errors": ["orders"],
        }

    if not args.user_id:
        return {"ok": True, "orders_summary": "", "error": "", "tool_errors": []}

    try:
        from apps.orders.models import Order

        def _run():
            orders = (
                Order.objects.filter(user_id=args.user_id)
                .prefetch_related("items")
                .order_by("-created_at")[:5]
            )
            lines: list[str] = []
            for order in orders:
                skus = ", ".join(i.sku for i in order.items.all()[:6])
                lines.append(f"{order.number} [{order.status}]: {skus or '—'}")
            return "\n".join(lines) if lines else "Nenhum pedido recente encontrado."

        summary = _with_db_retry(_run)
    except Exception:  # noqa: BLE001
        logger.exception("search_orders_failed")
        return {
            "ok": False,
            "orders_summary": "",
            "error": "orders_failed",
            "tool_errors": ["orders"],
        }

    return {"ok": True, "orders_summary": summary, "error": "", "tool_errors": []}
