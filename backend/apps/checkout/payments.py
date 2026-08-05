"""Gateways de pagamento tokenizados (mock / Stripe / Mercado Pago)."""

from __future__ import annotations

import hashlib
import hmac
import json
from dataclasses import dataclass
from decimal import Decimal

import structlog
from django.conf import settings

logger = structlog.get_logger(__name__)

# Campos proibidos em logs/persistência
FORBIDDEN_CARD_KEYS = frozenset(
    {
        "card_number",
        "number",
        "pan",
        "cvv",
        "cvc",
        "security_code",
        "card_cvv",
    }
)


@dataclass
class ChargeResult:
    success: bool
    provider_payment_id: str = ""
    provider_intent_id: str = ""
    status: str = "pending"
    last4: str = ""
    brand: str = ""
    failure_code: str = ""
    failure_message: str = ""
    raw: dict | None = None


def sanitize_payment_payload(data: dict) -> dict:
    """Remove qualquer campo sensível de cartão antes de logar/persistir."""
    clean = {}
    for k, v in data.items():
        if k.lower() in FORBIDDEN_CARD_KEYS:
            continue
        if isinstance(v, dict):
            clean[k] = sanitize_payment_payload(v)
        else:
            clean[k] = v
    return clean


def get_provider_name() -> str:
    return getattr(settings, "PAYMENT_PROVIDER", "mock").lower()


def create_charge(
    *,
    amount: Decimal,
    currency: str,
    payment_token: str,
    order_number: str,
    customer_email: str,
    metadata: dict | None = None,
) -> ChargeResult:
    provider = get_provider_name()
    meta = sanitize_payment_payload(metadata or {})
    logger.info(
        "payment_charge_start",
        provider=provider,
        order=order_number,
        amount=str(amount),
        token_prefix=(payment_token or "")[:8],
    )
    if provider == "stripe":
        return _charge_stripe(amount, currency, payment_token, order_number, customer_email, meta)
    if provider == "mercadopago":
        return _charge_mercadopago(
            amount, currency, payment_token, order_number, customer_email, meta
        )
    return _charge_mock(amount, payment_token, order_number)


def refund_charge(*, provider_payment_id: str, amount: Decimal | None = None) -> ChargeResult:
    provider = get_provider_name()
    if provider == "mock" or provider_payment_id.startswith("mock_"):
        return ChargeResult(
            success=True,
            provider_payment_id=provider_payment_id,
            status="refunded",
        )
    if provider == "stripe":
        return _refund_stripe(provider_payment_id, amount)
    if provider == "mercadopago":
        return _refund_mercadopago(provider_payment_id, amount)
    return ChargeResult(success=False, failure_message="Provider desconhecido", status="failed")


def verify_webhook_signature(*, payload: bytes, signature_header: str) -> bool:
    """Valida assinatura do webhook conforme provider."""
    provider = get_provider_name()
    if provider == "mock":
        secret = getattr(settings, "PAYMENT_WEBHOOK_SECRET", "dev-webhook-secret")
        expected = hmac.new(secret.encode(), payload, hashlib.sha256).hexdigest()
        return hmac.compare_digest(expected, signature_header or "")
    if provider == "stripe":
        return _verify_stripe_signature(payload, signature_header)
    if provider == "mercadopago":
        secret = getattr(settings, "MERCADOPAGO_WEBHOOK_SECRET", "")
        if not secret:
            return False
        expected = hmac.new(secret.encode(), payload, hashlib.sha256).hexdigest()
        return hmac.compare_digest(expected, signature_header or "")
    return False


def _charge_mock(amount: Decimal, payment_token: str, order_number: str) -> ChargeResult:
    token = (payment_token or "").strip()
    if token in {"tok_fail", "fail", "declined"}:
        return ChargeResult(
            success=False,
            status="failed",
            failure_code="card_declined",
            failure_message="Pagamento recusado (sandbox).",
            provider_payment_id=f"mock_fail_{order_number}",
        )
    return ChargeResult(
        success=True,
        status="paid",
        provider_payment_id=f"mock_pay_{order_number}",
        provider_intent_id=f"mock_intent_{order_number}",
        last4=token[-4:] if len(token) >= 4 else "4242",
        brand="visa",
        raw={"provider": "mock", "amount": str(amount)},
    )


def _charge_stripe(amount, currency, payment_token, order_number, email, meta) -> ChargeResult:
    try:
        import stripe
    except ImportError as exc:
        raise RuntimeError("stripe não instalado") from exc

    stripe.api_key = settings.STRIPE_SECRET_KEY
    try:
        intent = stripe.PaymentIntent.create(
            amount=int(amount * 100),
            currency=currency.lower(),
            payment_method=payment_token,
            confirm=True,
            receipt_email=email,
            metadata={"order": order_number, **{k: str(v) for k, v in meta.items()}},
            automatic_payment_methods={"enabled": True, "allow_redirects": "never"},
        )
        ok = intent.status in {"succeeded", "requires_capture"}
        return ChargeResult(
            success=ok,
            status="paid" if ok else intent.status,
            provider_payment_id=intent.id,
            provider_intent_id=intent.id,
            raw={"id": intent.id, "status": intent.status},
        )
    except Exception as exc:  # noqa: BLE001
        logger.warning("stripe_charge_failed", error=str(exc))
        return ChargeResult(
            success=False,
            status="failed",
            failure_message=str(exc)[:250],
            failure_code="stripe_error",
        )


def _charge_mercadopago(amount, currency, payment_token, order_number, email, meta) -> ChargeResult:
    try:
        import mercadopago
    except ImportError as exc:
        raise RuntimeError("mercadopago não instalado") from exc

    sdk = mercadopago.SDK(settings.MERCADOPAGO_ACCESS_TOKEN)
    payment_data = {
        "transaction_amount": float(amount),
        "token": payment_token,
        "description": f"Pedido {order_number}",
        "installments": 1,
        "payer": {"email": email},
        "external_reference": order_number,
        "metadata": meta,
    }
    result = sdk.payment().create(payment_data)
    resp = result.get("response", {})
    status = resp.get("status", "rejected")
    ok = status in {"approved", "authorized"}
    return ChargeResult(
        success=ok,
        status="paid" if ok else "failed",
        provider_payment_id=str(resp.get("id", "")),
        last4=str(resp.get("card", {}).get("last_four_digits", "")),
        brand=str(resp.get("payment_method_id", "")),
        failure_message="" if ok else str(resp.get("status_detail", "rejected")),
        raw=sanitize_payment_payload(resp) if isinstance(resp, dict) else {},
    )


def _refund_stripe(payment_id: str, amount: Decimal | None) -> ChargeResult:
    import stripe

    stripe.api_key = settings.STRIPE_SECRET_KEY
    kwargs = {"payment_intent": payment_id}
    if amount is not None:
        kwargs["amount"] = int(amount * 100)
    ref = stripe.Refund.create(**kwargs)
    return ChargeResult(success=True, provider_payment_id=ref.id, status="refunded")


def _refund_mercadopago(payment_id: str, amount: Decimal | None) -> ChargeResult:
    import mercadopago

    sdk = mercadopago.SDK(settings.MERCADOPAGO_ACCESS_TOKEN)
    body = {}
    if amount is not None:
        body["amount"] = float(amount)
    result = sdk.refund().create(payment_id, body)
    resp = result.get("response", {})
    return ChargeResult(
        success=True,
        provider_payment_id=str(resp.get("id", payment_id)),
        status="refunded",
        raw=resp if isinstance(resp, dict) else {},
    )


def _verify_stripe_signature(payload: bytes, header: str) -> bool:
    try:
        import stripe

        stripe.Webhook.construct_event(
            payload,
            header,
            settings.STRIPE_WEBHOOK_SECRET,
        )
        return True
    except Exception:  # noqa: BLE001
        return False


def parse_webhook_event(payload: bytes) -> dict:
    return json.loads(payload.decode("utf-8"))
