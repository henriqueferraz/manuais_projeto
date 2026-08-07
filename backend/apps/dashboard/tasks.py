"""Tasks Celery do dashboard (F7)."""

from __future__ import annotations

import structlog
from celery import shared_task

logger = structlog.get_logger(__name__)


@shared_task(name="dashboard.scan_alerts")
def scan_alerts_task() -> dict:
    from apps.dashboard.services.monitoring import scan_and_emit_alerts

    created = scan_and_emit_alerts()
    logger.info("dashboard_scan_alerts", count=len(created))
    return {"created": len(created), "ids": [str(a.pk) for a in created]}
