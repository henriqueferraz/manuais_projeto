"""Tasks Celery do pipeline de ingestão."""

from __future__ import annotations

import structlog
from celery import shared_task

logger = structlog.get_logger(__name__)


@shared_task(bind=True, name="manuals.extract_manual", max_retries=2, default_retry_delay=30)
def extract_manual_task(self, extraction_id: int) -> dict:
    from apps.manuals.services.pipeline import run_extraction

    logger.info("extract_manual_task_start", extraction_id=extraction_id, task_id=self.request.id)
    log = run_extraction(extraction_id)
    return {
        "extraction_id": log.pk,
        "status": log.status,
        "confidence": log.confidence,
        "cost_estimate": float(log.cost_estimate),
        "error": log.error_message[:500] if log.error_message else "",
    }
