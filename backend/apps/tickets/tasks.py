"""Tasks Celery — SLA de chamados e e-mail cross-sell."""

from __future__ import annotations

import structlog
from celery import shared_task
from django.core.mail import send_mail
from django.template.loader import render_to_string

from apps.notifications.models import EmailLog
from apps.orders.models import Order
from apps.tickets.services import check_sla_breaches, cross_sell_for_order

logger = structlog.get_logger(__name__)


@shared_task(name="tickets.check_sla")
def check_ticket_sla_task() -> dict:
    n = check_sla_breaches()
    logger.info("ticket_sla_checked", breached=n)
    return {"breached": n}


@shared_task(name="tickets.send_cross_sell_email")
def send_cross_sell_email_task(order_id: str) -> dict:
    order = Order.objects.prefetch_related("items__product").get(pk=order_id)
    suggestions = cross_sell_for_order(order)
    if not suggestions:
        return {"sent": False, "reason": "no_suggestions"}
    subject = f"Peças compatíveis para o pedido {order.number} — TechParts AI"
    body = render_to_string(
        "emails/cross_sell.txt",
        {"order": order, "suggestions": suggestions, "brand_name": "TechParts AI"},
    )
    log = EmailLog.objects.create(
        to_email=order.email,
        subject=subject,
        kind=EmailLog.Kind.OTHER,
        status=EmailLog.Status.QUEUED,
        order=order,
    )
    try:
        send_mail(subject, body, None, [order.email], fail_silently=False)
        log.status = EmailLog.Status.SENT
        log.save(update_fields=["status", "updated_at"])
        return {"sent": True, "count": len(suggestions)}
    except Exception as exc:  # noqa: BLE001
        log.status = EmailLog.Status.FAILED
        log.error_message = str(exc)[:2000]
        log.save(update_fields=["status", "error_message", "updated_at"])
        return {"sent": False, "error": str(exc)}
