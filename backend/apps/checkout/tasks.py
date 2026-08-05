"""Tasks Celery: NF-e e e-mails pós-pagamento."""

from __future__ import annotations

import uuid

import structlog
from celery import shared_task
from django.conf import settings
from django.core.mail import send_mail
from django.template.loader import render_to_string
from django.utils import timezone

from apps.notifications.models import EmailLog
from apps.orders.models import Invoice, Order

logger = structlog.get_logger(__name__)


@shared_task(bind=True, name="checkout.emit_invoice", max_retries=3, default_retry_delay=60)
def emit_invoice_task(self, order_id: str) -> dict:
    order = Order.objects.get(pk=order_id)
    invoice, _ = Invoice.objects.get_or_create(order=order)
    invoice.status = Invoice.Status.PROCESSING
    invoice.attempts += 1
    invoice.save(update_fields=["status", "attempts", "updated_at"])

    try:
        result = _emit_nfe(order, invoice)
        invoice.status = Invoice.Status.ISSUED
        invoice.access_key = result["access_key"]
        invoice.number = result["number"]
        invoice.series = result["series"]
        invoice.pdf_url = result.get("pdf_url", "")
        invoice.xml_url = result.get("xml_url", "")
        invoice.error_message = ""
        invoice.issued_at = timezone.now()
        invoice.save()
        send_invoice_email_task.delay(order_id)
        logger.info("nfe_issued", order=order.number, number=invoice.number)
        return {"status": "issued", "number": invoice.number}
    except Exception as exc:  # noqa: BLE001
        invoice.status = Invoice.Status.FAILED
        invoice.error_message = str(exc)[:2000]
        invoice.save(update_fields=["status", "error_message", "updated_at"])
        logger.exception("nfe_failed", order=order.number)
        # Reagenda sem derrubar o fluxo de pagamento (eager Celery)
        if self.request.retries < self.max_retries:
            raise self.retry(exc=exc) from exc
        return {"status": "failed", "error": str(exc)}


def _emit_nfe(order: Order, invoice: Invoice) -> dict:
    """Provedor fiscal — mock por padrão; plugável via NFE_PROVIDER."""
    provider = getattr(settings, "NFE_PROVIDER", "mock")
    if provider != "mock":
        # Placeholder para Focus NFe / NFe.io / etc.
        raise RuntimeError(f"Provedor NF-e '{provider}' ainda não implementado.")

    # Simula falha controlada para testes
    if order.notes == "force_nfe_fail":
        raise RuntimeError("Falha simulada na API fiscal.")

    key = (uuid.uuid4().hex + uuid.uuid4().hex)[:44]
    number = str(1000 + invoice.attempts)
    return {
        "access_key": key,
        "number": number,
        "series": "1",
        "pdf_url": f"https://example.local/nfe/{order.number}.pdf",
        "xml_url": f"https://example.local/nfe/{order.number}.xml",
    }


@shared_task(name="checkout.send_order_emails")
def send_order_emails_task(order_id: str) -> dict:
    order = Order.objects.prefetch_related("items").get(pk=order_id)
    subject = f"Pedido {order.number} confirmado — TechParts AI"
    body = render_to_string(
        "emails/order_confirmation.txt",
        {"order": order, "brand_name": "TechParts AI"},
    )
    return _send_logged_email(
        to_email=order.email,
        subject=subject,
        body=body,
        kind=EmailLog.Kind.ORDER_CONFIRMATION,
        order=order,
    )


@shared_task(name="checkout.send_invoice_email")
def send_invoice_email_task(order_id: str) -> dict:
    order = Order.objects.select_related("invoice").get(pk=order_id)
    invoice = order.invoice
    subject = f"NF-e do pedido {order.number} — TechParts AI"
    body = render_to_string(
        "emails/invoice.txt",
        {"order": order, "invoice": invoice, "brand_name": "TechParts AI"},
    )
    return _send_logged_email(
        to_email=order.email,
        subject=subject,
        body=body,
        kind=EmailLog.Kind.INVOICE,
        order=order,
    )


def _send_logged_email(*, to_email, subject, body, kind, order) -> dict:
    log = EmailLog.objects.create(
        to_email=to_email,
        subject=subject,
        kind=kind,
        status=EmailLog.Status.QUEUED,
        order=order,
    )
    try:
        send_mail(
            subject,
            body,
            getattr(settings, "DEFAULT_FROM_EMAIL", "noreply@techparts.local"),
            [to_email],
            fail_silently=False,
        )
        log.status = EmailLog.Status.SENT
        log.save(update_fields=["status", "updated_at"])
        return {"status": "sent", "log_id": log.pk}
    except Exception as exc:  # noqa: BLE001
        log.status = EmailLog.Status.FAILED
        log.error_message = str(exc)[:2000]
        log.save(update_fields=["status", "error_message", "updated_at"])
        logger.exception("email_failed", to=to_email)
        return {"status": "failed", "error": str(exc)}


@shared_task(name="checkout.record_email_bounce")
def record_email_bounce_task(to_email: str, detail: str = "") -> int:
    updated = EmailLog.objects.filter(
        to_email=to_email,
        status=EmailLog.Status.SENT,
    ).update(status=EmailLog.Status.BOUNCED, bounce_detail=detail[:2000])
    return updated
