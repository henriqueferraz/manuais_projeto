"""Orquestração do checkout: pedido → pagamento → estoque → NF-e/e-mail."""

from __future__ import annotations

from decimal import Decimal

import structlog
from django.core.exceptions import ValidationError
from django.db import transaction
from django.utils import timezone

from apps.cart.models import Cart
from apps.cart.services import cart_totals
from apps.checkout.payments import create_charge, get_provider_name, refund_charge
from apps.checkout.shipping import calculate_shipping, pick_option
from apps.orders.models import Invoice, Order, OrderItem, Payment
from apps.products.models import Stock

logger = structlog.get_logger(__name__)


def build_order_from_cart(
    *,
    cart: Cart,
    email: str,
    shipping: dict,
    shipping_option_id: str,
    user=None,
) -> Order:
    totals = cart_totals(cart)
    if not totals["items"]:
        raise ValidationError("Carrinho vazio.")

    weight = Decimal("0")
    for item in totals["items"]:
        w = item.product.weight_kg or Decimal("0.5")
        weight += w * item.quantity

    options = calculate_shipping(
        cep=shipping["shipping_cep"],
        subtotal=totals["subtotal"],
        weight_kg=weight,
    )
    option = pick_option(options, shipping_option_id)

    with transaction.atomic():
        order = Order.objects.create(
            number=Order.next_number(),
            user=user if getattr(user, "is_authenticated", False) else None,
            email=email,
            status=Order.Status.AWAITING_PAYMENT,
            shipping_name=shipping["shipping_name"],
            shipping_phone=shipping.get("shipping_phone", ""),
            shipping_cep=shipping["shipping_cep"],
            shipping_street=shipping["shipping_street"],
            shipping_number=shipping["shipping_number"],
            shipping_complement=shipping.get("shipping_complement", ""),
            shipping_district=shipping["shipping_district"],
            shipping_city=shipping["shipping_city"],
            shipping_state=shipping["shipping_state"].upper()[:2],
            shipping_method=option.service,
            shipping_carrier=option.carrier,
            shipping_quote_id=option.id,
            shipping_cost=option.price,
            shipping_eta_days=option.eta_days,
            subtotal=totals["subtotal"],
            total=totals["subtotal"] + option.price,
            cart=cart,
        )
        for item in totals["items"]:
            OrderItem.objects.create(
                order=order,
                product=item.product,
                sku=item.product.sku,
                name=item.product.name_pt,
                quantity=item.quantity,
                unit_price=item.unit_price,
                line_total=item.line_total,
            )
    return order


def pay_order(*, order: Order, payment_token: str) -> Payment:
    if order.status not in {
        Order.Status.AWAITING_PAYMENT,
        Order.Status.PAYMENT_FAILED,
    }:
        raise ValidationError(f"Pedido não pode ser pago no status {order.status}.")

    provider = get_provider_name()
    with transaction.atomic():
        payment = Payment.objects.create(
            order=order,
            provider=provider,
            amount=order.total,
            currency=order.currency,
            payment_token=payment_token[:64],  # só referência/token, nunca PAN
            status=Payment.Status.PENDING,
        )

        result = create_charge(
            amount=order.total,
            currency=order.currency,
            payment_token=payment_token,
            order_number=order.number,
            customer_email=order.email,
            metadata={"order_id": str(order.id)},
        )

        payment.provider_payment_id = result.provider_payment_id
        payment.provider_intent_id = result.provider_intent_id
        payment.last4 = result.last4
        payment.brand = result.brand
        payment.failure_code = result.failure_code
        payment.failure_message = result.failure_message
        if result.raw:
            payment.raw_webhook = result.raw

        if result.success:
            payment.status = Payment.Status.PAID
            payment.save()
            _mark_order_paid(order)
            return payment

        payment.status = Payment.Status.FAILED
        payment.save()
        order.status = Order.Status.PAYMENT_FAILED
        order.save(update_fields=["status", "updated_at"])

    raise ValidationError(result.failure_message or "Pagamento recusado.")


def _mark_order_paid(order: Order) -> None:
    order.status = Order.Status.PAID
    order.paid_at = timezone.now()
    order.save(update_fields=["status", "paid_at", "updated_at"])

    for item in order.items.select_related("product"):
        if item.product_id:
            Stock.commit_sale(item.product_id, item.quantity)

    if order.cart_id:
        order.cart.items.all().delete()

    Invoice.objects.get_or_create(order=order, defaults={"status": Invoice.Status.PENDING})

    from apps.checkout.tasks import emit_invoice_task, send_order_emails_task

    emit_invoice_task.delay(str(order.id))
    send_order_emails_task.delay(str(order.id))


@transaction.atomic
def apply_payment_webhook(
    *, provider_payment_id: str, event_status: str, raw: dict
) -> Payment | None:
    payment = (
        Payment.objects.select_for_update()
        .select_related("order")
        .filter(provider_payment_id=provider_payment_id)
        .first()
    )
    if payment is None:
        return None

    payment.raw_webhook = raw
    if event_status in {"paid", "succeeded", "approved"}:
        payment.status = Payment.Status.PAID
        payment.save()
        if payment.order.status != Order.Status.PAID:
            _mark_order_paid(payment.order)
    elif event_status in {"failed", "rejected", "canceled", "cancelled"}:
        payment.status = Payment.Status.FAILED
        payment.save()
        payment.order.status = Order.Status.PAYMENT_FAILED
        payment.order.save(update_fields=["status", "updated_at"])
    elif event_status in {"refunded"}:
        payment.status = Payment.Status.REFUNDED
        payment.save()
        payment.order.status = Order.Status.REFUNDED
        payment.order.save(update_fields=["status", "updated_at"])
    else:
        payment.save(update_fields=["raw_webhook", "updated_at"])
    return payment


@transaction.atomic
def refund_order_payment(order: Order) -> Payment:
    payment = order.payments.filter(status=Payment.Status.PAID).order_by("-created_at").first()
    if payment is None:
        raise ValidationError("Nenhum pagamento pago para estornar.")
    result = refund_charge(provider_payment_id=payment.provider_payment_id, amount=payment.amount)
    if not result.success:
        raise ValidationError(result.failure_message or "Falha no estorno.")
    payment.status = Payment.Status.REFUNDED
    payment.save(update_fields=["status", "updated_at"])
    order.status = Order.Status.REFUNDED
    order.save(update_fields=["status", "updated_at"])
    return payment
