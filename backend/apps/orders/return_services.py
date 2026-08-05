"""Serviços de troca/devolução (CDC)."""

from __future__ import annotations

from django.core.exceptions import ValidationError
from django.db import transaction
from django.utils import timezone

from apps.checkout.services import refund_order_payment
from apps.orders.models import Order, ReturnRequest


@transaction.atomic
def create_return_request(
    *,
    order: Order,
    email: str,
    kind: str,
    reason: str,
    details: str = "",
    delivered_at=None,
    user=None,
) -> ReturnRequest:
    if order.status not in {Order.Status.PAID, Order.Status.FULFILLED}:
        raise ValidationError("Pedido não elegível para devolução.")

    delivered = delivered_at or order.paid_at or timezone.now()
    deadline = ReturnRequest.compute_deadline(delivered)
    if timezone.now() > deadline and reason == ReturnRequest.Reason.REGRET:
        raise ValidationError(
            "Prazo de arrependimento de 7 dias (CDC) expirado a partir da entrega."
        )

    return ReturnRequest.objects.create(
        order=order,
        email=email,
        kind=kind,
        reason=reason,
        details=details,
        user=user if getattr(user, "is_authenticated", False) else None,
        delivered_at=delivered,
        deadline_at=deadline,
        status=ReturnRequest.Status.REQUESTED,
    )


@transaction.atomic
def process_return(
    request_obj: ReturnRequest,
    *,
    approve: bool,
    staff_notes: str = "",
) -> ReturnRequest:
    if request_obj.status not in {
        ReturnRequest.Status.REQUESTED,
        ReturnRequest.Status.UNDER_REVIEW,
        ReturnRequest.Status.APPROVED,
    }:
        raise ValidationError("Solicitação em status final.")

    request_obj.staff_notes = staff_notes
    if not approve:
        request_obj.status = ReturnRequest.Status.REJECTED
        request_obj.save()
        return request_obj

    request_obj.status = ReturnRequest.Status.APPROVED
    request_obj.save(update_fields=["status", "staff_notes", "updated_at"])

    if request_obj.kind == ReturnRequest.Kind.REFUND:
        payment = refund_order_payment(request_obj.order)
        request_obj.status = ReturnRequest.Status.REFUNDED
        request_obj.refund_payment_id = str(payment.pk)
        request_obj.save(update_fields=["status", "refund_payment_id", "updated_at"])
    else:
        request_obj.status = ReturnRequest.Status.EXCHANGED
        request_obj.save(update_fields=["status", "updated_at"])
    return request_obj
