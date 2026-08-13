"""Orquestração do checkout: pedido → pagamento → estoque → NF-e/e-mail."""

from __future__ import annotations

from decimal import Decimal

import structlog
from django.core.exceptions import ValidationError
from django.db import transaction
from django.utils import timezone

from apps.cart.models import Cart
from apps.cart.services import cart_totals
from apps.checkout.payments import (
    create_charge,
    create_mercadopago_preference,
    fetch_mercadopago_payment,
    get_provider_name,
    mercadopago_uses_preference,
    public_base_url,
    refund_charge,
)
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
    coupon_code: str = "",
    attribution_source: str = "",
    chat_session_id: str | None = None,
) -> Order:
    """Cria Order + itens a partir do carrinho (frete, cupom, atribuição)."""
    from apps.cart.coupons import cart_totals_with_coupon

    if coupon_code:
        totals = cart_totals_with_coupon(cart, coupon_code)
    else:
        totals = cart_totals(cart)
        totals["discount"] = Decimal("0")
        totals["total_after_discount"] = totals["subtotal"]

    if not totals["items"]:
        raise ValidationError("Carrinho vazio.")

    weight = Decimal("0")
    for item in totals["items"]:
        w = item.product.weight_kg or Decimal("0.5")
        weight += w * item.quantity

    taxable = totals["total_after_discount"]
    options = calculate_shipping(
        cep=shipping["shipping_cep"],
        subtotal=taxable,
        weight_kg=weight,
    )
    option = pick_option(options, shipping_option_id)

    with transaction.atomic():
        source = attribution_source or Order.AttributionSource.DIRECT
        if source not in Order.AttributionSource.values:
            source = Order.AttributionSource.DIRECT
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
            discount=totals["discount"],
            coupon_code=(coupon_code or "").upper(),
            total=taxable + option.price,
            cart=cart,
            attribution_source=source,
            chat_session_id=chat_session_id or None,
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
        if totals.get("coupon"):
            coupon = totals["coupon"]
            coupon.used_count += 1
            coupon.save(update_fields=["used_count"])
    return order


def pay_order(*, order: Order, payment_token: str, charge_extra: dict | None = None) -> Payment:
    """Cobra o pedido; em sucesso marca pago, baixa estoque e dispara NF-e/e-mail.

    Args:
        charge_extra: payload do Card Payment Brick (Checkout Transparente).
    """
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
            charge_extra=charge_extra,
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


def start_mercadopago_preference_checkout(*, order: Order) -> str:
    """Cria Payment pendente + Preference MP e devolve a URL de checkout.

    Raises:
        ValidationError: se a Preference falhar.
    """
    if not mercadopago_uses_preference():
        raise ValidationError("Checkout Preference do Mercado Pago não está ativo.")
    if order.status not in {
        Order.Status.AWAITING_PAYMENT,
        Order.Status.PAYMENT_FAILED,
    }:
        raise ValidationError(f"Pedido não pode ser pago no status {order.status}.")

    base = public_base_url()
    success_url = f"{base}/checkout/sucesso/{order.id}/"
    failure_url = f"{base}/checkout/pagamento/?mp=failure&order={order.id}"
    pending_url = f"{base}/checkout/sucesso/{order.id}/?mp=pending"
    notification_url = f"{base}/checkout/webhooks/pagamento/"

    items = [
        {
            "id": item.sku,
            "title": (item.name or item.sku)[:127],
            "quantity": int(item.quantity),
            "currency_id": (order.currency or "BRL").upper(),
            "unit_price": float(item.unit_price),
        }
        for item in order.items.all()
    ]
    if order.shipping_cost and order.shipping_cost > 0:
        items.append(
            {
                "id": "shipping",
                "title": "Frete",
                "quantity": 1,
                "currency_id": (order.currency or "BRL").upper(),
                "unit_price": float(order.shipping_cost),
            }
        )
    line_sum = sum((i.line_total for i in order.items.all()), Decimal("0")) + (
        order.shipping_cost or Decimal("0")
    )
    if order.discount and order.discount > 0 and line_sum != order.total:
        items = [
            {
                "id": order.number,
                "title": f"Pedido {order.number}",
                "quantity": 1,
                "currency_id": (order.currency or "BRL").upper(),
                "unit_price": float(order.total),
            }
        ]

    pref = create_mercadopago_preference(
        order_number=order.number,
        order_id=str(order.id),
        amount=order.total,
        currency=order.currency or "BRL",
        title=f"Pedido {order.number}",
        payer_email=order.email,
        items=items,
        success_url=success_url,
        failure_url=failure_url,
        pending_url=pending_url,
        notification_url=notification_url,
    )
    if not pref.success:
        raise ValidationError(pref.failure_message or "Falha ao criar Preference no Mercado Pago.")

    with transaction.atomic():
        payment = Payment.objects.create(
            order=order,
            provider=Payment.Provider.MERCADOPAGO,
            amount=order.total,
            currency=order.currency,
            payment_token="",
            status=Payment.Status.PENDING,
            provider_intent_id=pref.preference_id,
            raw_webhook=pref.raw or {},
        )
        order.status = Order.Status.AWAITING_PAYMENT
        order.save(update_fields=["status", "updated_at"])
        logger.info(
            "mp_preference_checkout_started",
            order=order.number,
            preference_id=pref.preference_id,
            payment_id=str(payment.id),
        )

    url = pref.checkout_url
    if not url:
        raise ValidationError("Preference criada sem URL de checkout.")
    return url


def sync_mercadopago_payment_by_id(payment_id: str) -> Payment | None:
    """Busca pagamento no MP e atualiza Order/Payment local via external_reference."""
    if not payment_id:
        return None
    try:
        resp = fetch_mercadopago_payment(str(payment_id))
    except Exception as exc:  # noqa: BLE001
        logger.warning("mp_payment_fetch_failed", payment_id=payment_id, error=str(exc)[:200])
        return None

    status_mp = str(resp.get("status") or "")
    external = str(resp.get("external_reference") or "")
    if status_mp in {"approved", "authorized"}:
        event_status = "paid"
    elif status_mp in {"rejected", "cancelled", "canceled"}:
        event_status = "failed"
    elif status_mp in {"refunded", "charged_back"}:
        event_status = "refunded"
    else:
        event_status = status_mp or "pending"

    return apply_payment_webhook(
        provider_payment_id=str(resp.get("id") or payment_id),
        event_status=event_status,
        raw=resp,
        external_reference=external,
        preference_id=str(resp.get("preference_id") or ""),
    )


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
    from apps.tickets.tasks import send_cross_sell_email_task

    emit_invoice_task.delay(str(order.id))
    send_order_emails_task.delay(str(order.id))
    send_cross_sell_email_task.delay(str(order.id))


@transaction.atomic
def apply_payment_webhook(
    *,
    provider_payment_id: str,
    event_status: str,
    raw: dict,
    external_reference: str = "",
    preference_id: str = "",
) -> Payment | None:
    """Atualiza Payment/Order a partir do webhook do provedor; None se id desconhecido."""
    payment = (
        Payment.objects.select_for_update()
        .select_related("order")
        .filter(provider_payment_id=provider_payment_id)
        .first()
    )
    if payment is None and preference_id:
        payment = (
            Payment.objects.select_for_update()
            .select_related("order")
            .filter(provider_intent_id=preference_id, status=Payment.Status.PENDING)
            .order_by("-created_at")
            .first()
        )
    if payment is None and external_reference:
        payment = (
            Payment.objects.select_for_update()
            .select_related("order")
            .filter(order__number=external_reference, status=Payment.Status.PENDING)
            .order_by("-created_at")
            .first()
        )
    if payment is None:
        return None

    if provider_payment_id and not payment.provider_payment_id:
        payment.provider_payment_id = str(provider_payment_id)

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
        payment.save(update_fields=["raw_webhook", "provider_payment_id", "updated_at"])
    return payment


@transaction.atomic
def refund_order_payment(order: Order) -> Payment:
    """Estorna o pagamento pago mais recente e marca o pedido como reembolsado."""
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
