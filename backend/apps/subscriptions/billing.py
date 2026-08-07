"""Billing de assinaturas (mock / Stripe / Mercado Pago) — T-P.4 / ADR-0004."""

from __future__ import annotations

from dataclasses import dataclass
from datetime import timedelta

import structlog
from django.conf import settings
from django.utils import timezone

from apps.subscriptions.models import Subscription, SubscriptionPlan

logger = structlog.get_logger(__name__)


@dataclass
class BillingResult:
    success: bool
    subscription: Subscription | None = None
    provider_subscription_id: str = ""
    failure_message: str = ""


def get_billing_mode() -> str:
    return (getattr(settings, "SUBSCRIPTION_BILLING_MODE", "mock") or "mock").lower()


def start_subscription(
    *,
    plan: SubscriptionPlan,
    email: str,
    user=None,
    payment_token: str = "",
) -> BillingResult:
    mode = get_billing_mode()
    if mode == "mock":
        sub = Subscription.start_mock(plan=plan, email=email, user=user)
        return BillingResult(success=True, subscription=sub, provider_subscription_id="mock")
    if mode == "stripe":
        return _start_stripe(plan=plan, email=email, user=user, payment_token=payment_token)
    if mode == "mercadopago":
        return _start_mercadopago(plan=plan, email=email, user=user, payment_token=payment_token)
    return BillingResult(success=False, failure_message=f"Modo de billing desconhecido: {mode}")


def _persist_local(
    *,
    plan: SubscriptionPlan,
    email: str,
    user,
    provider_id: str,
    status: str = Subscription.Status.ACTIVE,
) -> Subscription:
    return Subscription.objects.create(
        plan=plan,
        email=email,
        user=user if getattr(user, "is_authenticated", False) else None,
        status=status,
        current_period_end=timezone.now() + timedelta(days=plan.interval_days),
        provider_subscription_id=provider_id,
        billing_provider=get_billing_mode(),
    )


def _start_stripe(*, plan, email, user, payment_token) -> BillingResult:
    try:
        import stripe
    except ImportError as exc:
        raise RuntimeError("stripe não instalado") from exc

    stripe.api_key = settings.STRIPE_SECRET_KEY
    price_id = getattr(plan, "stripe_price_id", "") or getattr(
        settings, "STRIPE_SUBSCRIPTION_PRICE_MAP", {}
    ).get(plan.code, "")
    if not price_id and not payment_token:
        return BillingResult(
            success=False,
            failure_message="Configure stripe_price_id no plano ou payment_token.",
        )
    try:
        customer = stripe.Customer.create(email=email)
        kwargs: dict = {
            "customer": customer.id,
            "items": [{"price": price_id}] if price_id else [],
            "metadata": {"plan": plan.code},
        }
        if payment_token:
            kwargs["default_payment_method"] = payment_token
            if not price_id:
                # Cobrança única recorrente via price_data quando não há Price pré-criado
                kwargs["items"] = [
                    {
                        "price_data": {
                            "currency": (plan.currency or "brl").lower(),
                            "unit_amount": int(plan.price_monthly * 100),
                            "recurring": {"interval": "month"},
                            "product_data": {"name": plan.name},
                        }
                    }
                ]
        sub_remote = stripe.Subscription.create(**kwargs)
        local = _persist_local(
            plan=plan,
            email=email,
            user=user,
            provider_id=sub_remote.id,
        )
        logger.info("subscription_stripe_created", id=sub_remote.id, plan=plan.code)
        return BillingResult(
            success=True,
            subscription=local,
            provider_subscription_id=sub_remote.id,
        )
    except Exception as exc:  # noqa: BLE001
        logger.warning("subscription_stripe_failed", error=str(exc)[:240])
        return BillingResult(success=False, failure_message=str(exc)[:250])


def _start_mercadopago(*, plan, email, user, payment_token) -> BillingResult:
    """
    Cria pré-aprovação / assinatura MP.
    Em sandbox sem token, falha com mensagem clara (CI permanece mock).
    """
    try:
        import mercadopago
    except ImportError as exc:
        raise RuntimeError("mercadopago não instalado") from exc

    if not payment_token:
        return BillingResult(
            success=False,
            failure_message="payment_token obrigatório para assinatura Mercado Pago.",
        )
    sdk = mercadopago.SDK(settings.MERCADOPAGO_ACCESS_TOKEN)
    body = {
        "reason": plan.name,
        "external_reference": plan.code,
        "payer_email": email,
        "auto_recurring": {
            "frequency": 1,
            "frequency_type": "months",
            "transaction_amount": float(plan.price_monthly),
            "currency_id": plan.currency or "BRL",
        },
        "card_token_id": payment_token,
        "status": "authorized",
    }
    result = sdk.preapproval().create(body)
    resp = result.get("response", {})
    pre_id = str(resp.get("id") or "")
    if not pre_id:
        return BillingResult(
            success=False,
            failure_message=str(resp.get("message") or resp or "MP rejeitou"),
        )
    local = _persist_local(plan=plan, email=email, user=user, provider_id=pre_id)
    return BillingResult(success=True, subscription=local, provider_subscription_id=pre_id)
