"""Tasks Celery de indexação RAG e busca por foto."""

from __future__ import annotations

import structlog
from celery import shared_task

logger = structlog.get_logger(__name__)


@shared_task(bind=True, name="ai.index_manual", max_retries=1, default_retry_delay=20)
def index_manual_task(self, manual_id: int) -> dict:
    from apps.ai.services.retrieval import index_manual

    logger.info("index_manual_task_start", manual_id=manual_id, task_id=self.request.id)
    try:
        count = index_manual(manual_id)
    except Exception as exc:  # noqa: BLE001
        logger.exception("index_manual_task_failed", manual_id=manual_id)
        if self.request.retries < self.max_retries:
            raise self.retry(exc=exc) from exc
        return {"manual_id": manual_id, "chunks": 0, "error": str(exc)[:500]}
    return {"manual_id": manual_id, "chunks": count}


@shared_task(bind=True, name="ai.photo_search", max_retries=1, default_retry_delay=15)
def photo_search_task(self, search_id: str) -> dict:
    from apps.ai.services.photo_search import run_photo_search

    logger.info("photo_search_task_start", search_id=search_id, task_id=self.request.id)
    try:
        search = run_photo_search(search_id)
    except Exception as exc:  # noqa: BLE001
        logger.exception("photo_search_task_failed", search_id=search_id)
        if self.request.retries < self.max_retries:
            raise self.retry(exc=exc) from exc
        return {"search_id": search_id, "status": "failed", "error": str(exc)[:500]}
    return {
        "search_id": str(search.pk),
        "status": search.status,
        "candidates": len(search.candidates or []),
    }
