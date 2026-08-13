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
    """Resultado de cobrança tokenizada (mock / Stripe / Mercado Pago)."""

    success: bool
    provider_payment_id: str = ""
    provider_intent_id: str = ""
    status: str = "pending"
    last4: str = ""
    brand: str = ""
    failure_code: str = ""
    failure_message: str = ""
    raw: dict | None = None


@dataclass
class PreferenceResult:
    """Resultado da Preference (Checkout Pro) do Mercado Pago."""

    success: bool
    preference_id: str = ""
    init_point: str = ""
    sandbox_init_point: str = ""
    failure_message: str = ""
    raw: dict | None = None

    @property
    def checkout_url(self) -> str:
        """URL de redirecionamento (sandbox_init_point em DEBUG se existir)."""
        from django.conf import settings as dj_settings

        if getattr(dj_settings, "DEBUG", False) and self.sandbox_init_point:
            return self.sandbox_init_point
        return self.init_point or self.sandbox_init_point


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
    """Nome do gateway configurado (`mock` | `stripe` | `mercadopago`)."""
    return getattr(settings, "PAYMENT_PROVIDER", "mock").lower()


def mercadopago_uses_preference() -> bool:
    """True se MP deve usar Checkout Pro (Preference) em vez de card token."""
    if get_provider_name() != "mercadopago":
        return False
    mode = (getattr(settings, "MERCADOPAGO_CHECKOUT_MODE", "preference") or "preference").lower()
    return mode == "preference"


def public_base_url() -> str:
    """Base absoluta para back_urls e notification_url."""
    return (getattr(settings, "PUBLIC_BASE_URL", "") or "http://127.0.0.1:8000").rstrip("/")


def create_mercadopago_preference(
    *,
    order_number: str,
    order_id: str,
    amount: Decimal,
    currency: str,
    title: str,
    payer_email: str,
    items: list[dict] | None = None,
    success_url: str = "",
    failure_url: str = "",
    pending_url: str = "",
    notification_url: str = "",
) -> PreferenceResult:
    """Cria Preference (Checkout Pro) no Mercado Pago.

    Args:
        order_number: `external_reference` do pedido.
        items: itens opcionais; se vazio, usa um item único com `amount`/`title`.
        success_url / failure_url / pending_url: back_urls do Checkout Pro.
        notification_url: IPN/webhook.

    Returns:
        PreferenceResult com `init_point` / `sandbox_init_point`.
    """
    try:
        import mercadopago
    except ImportError as exc:
        raise RuntimeError("mercadopago não instalado") from exc

    token = getattr(settings, "MERCADOPAGO_ACCESS_TOKEN", "") or ""
    if not token:
        return PreferenceResult(
            success=False,
            failure_message="MERCADOPAGO_ACCESS_TOKEN não configurado.",
        )

    base = public_base_url()
    success_url = success_url or f"{base}/checkout/sucesso/{order_id}/"
    failure_url = failure_url or f"{base}/checkout/pagamento/?mp=failure"
    pending_url = pending_url or f"{base}/checkout/sucesso/{order_id}/?mp=pending"
    notification_url = notification_url or f"{base}/checkout/webhooks/pagamento/"

    if items:
        pref_items = items
    else:
        pref_items = [
            {
                "id": order_number,
                "title": (title or f"Pedido {order_number}")[:127],
                "quantity": 1,
                "currency_id": (currency or "BRL").upper(),
                "unit_price": float(amount),
            }
        ]

    body: dict = {
        "items": pref_items,
        "payer": {"email": payer_email},
        "external_reference": order_number,
        "back_urls": {
            "success": success_url,
            "failure": failure_url,
            "pending": pending_url,
        },
        "metadata": {"order_id": str(order_id), "order_number": order_number},
        "statement_descriptor": "TECHPARTS",
    }
    # auto_return exige back_urls.success em HTTPS (MP rejeita http://localhost).
    if success_url.startswith("https://"):
        body["auto_return"] = "approved"
    # notification_url precisa ser URL pública válida (não localhost/127.0.0.1).
    if notification_url.startswith("https://") and "localhost" not in notification_url:
        body["notification_url"] = notification_url

    sdk = mercadopago.SDK(token)
    try:
        result = sdk.preference().create(body)
    except Exception as exc:  # noqa: BLE001
        logger.warning("mp_preference_failed", error=str(exc)[:240])
        return PreferenceResult(success=False, failure_message=str(exc)[:250])

    resp = result.get("response", {}) if isinstance(result, dict) else {}
    pref_id = str(resp.get("id") or "")
    init_point = str(resp.get("init_point") or "")
    sandbox = str(resp.get("sandbox_init_point") or "")
    if not pref_id or not (init_point or sandbox):
        msg = str(resp.get("message") or resp.get("error") or resp or "Preference rejeitada")
        logger.warning("mp_preference_rejected", response=sanitize_payment_payload(resp))
        return PreferenceResult(success=False, failure_message=msg[:250], raw=resp)

    logger.info(
        "mp_preference_created",
        preference_id=pref_id,
        order=order_number,
    )
    return PreferenceResult(
        success=True,
        preference_id=pref_id,
        init_point=init_point,
        sandbox_init_point=sandbox,
        raw=sanitize_payment_payload(resp) if isinstance(resp, dict) else {},
    )


def fetch_mercadopago_payment(payment_id: str) -> dict:
    """Busca um pagamento no MP pelo id (webhook / back_url)."""
    import mercadopago

    sdk = mercadopago.SDK(settings.MERCADOPAGO_ACCESS_TOKEN)
    result = sdk.payment().get(payment_id)
    resp = result.get("response", {}) if isinstance(result, dict) else {}
    return resp if isinstance(resp, dict) else {}


def create_charge(
    *,
    amount: Decimal,
    currency: str,
    payment_token: str,
    order_number: str,
    customer_email: str,
    metadata: dict | None = None,
) -> ChargeResult:
    """Cria cobrança no provider configurado (`PAYMENT_PROVIDER`)."""
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
    """Estorna cobrança no provider (ou mock)."""
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
        # IPN/webhook: autenticidade via GET do pagamento na API (ACCESS_TOKEN).
        return True
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
    """Decodifica o corpo JSON do webhook."""
    return json.loads(payload.decode("utf-8"))
