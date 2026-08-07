"""Webhook WhatsApp (F8 / ADR-0002)."""

from __future__ import annotations

import hashlib
import hmac
import json

import structlog
from django.conf import settings
from django.http import HttpRequest, HttpResponse, JsonResponse
from django.views.decorators.csrf import csrf_exempt
from django.views.decorators.http import require_http_methods

from apps.ai.models import ChatSession
from apps.ai.services.diagnosis import diagnose_question
from apps.core.ratelimit import ai_rate_limit, record_token_usage

logger = structlog.get_logger(__name__)


def _verify_signature(request: HttpRequest) -> bool:
    secret = getattr(settings, "WHATSAPP_APP_SECRET", "") or ""
    if not secret:
        # Em mock/dev sem secret, aceita (CI). Produção deve setar secret.
        return getattr(settings, "WHATSAPP_MODE", "mock") == "mock"
    sig = request.headers.get("X-Hub-Signature-256") or ""
    if not sig.startswith("sha256="):
        return False
    expected = hmac.new(secret.encode(), request.body, hashlib.sha256).hexdigest()
    return hmac.compare_digest(sig.removeprefix("sha256="), expected)


@csrf_exempt
@require_http_methods(["GET", "POST"])
@ai_rate_limit
def whatsapp_webhook(request: HttpRequest) -> HttpResponse:
    if request.method == "GET":
        mode = request.GET.get("hub.mode")
        token = request.GET.get("hub.verify_token")
        challenge = request.GET.get("hub.challenge", "")
        expected = getattr(settings, "WHATSAPP_VERIFY_TOKEN", "") or "techparts-dev"
        if mode == "subscribe" and token == expected:
            return HttpResponse(challenge, content_type="text/plain")
        return HttpResponse("forbidden", status=403)

    if not _verify_signature(request):
        return JsonResponse({"detail": "Assinatura inválida."}, status=403)

    try:
        payload = json.loads(request.body.decode("utf-8") or "{}")
    except json.JSONDecodeError:
        return JsonResponse({"detail": "JSON inválido."}, status=400)

    text, wa_from = _extract_inbound(payload)
    if not text:
        return JsonResponse({"ok": True, "ignored": True})

    session = ChatSession.objects.create(anonymous_key=f"wa:{wa_from or 'unknown'}"[:64])
    assistant, stream, meta = diagnose_question(
        session, text, request_id=getattr(request, "request_id", "")
    )
    reply = "".join(stream) or assistant.content
    record_token_usage(assistant.tokens_in + assistant.tokens_out)
    _send_outbound(wa_from, reply)

    logger.info(
        "whatsapp_inbound",
        from_id=wa_from,
        session_id=str(session.pk),
        mode=meta.get("mode"),
    )
    return JsonResponse(
        {
            "ok": True,
            "session_id": str(session.pk),
            "reply_preview": reply[:240],
            "outbound": getattr(settings, "WHATSAPP_MODE", "mock"),
        }
    )


def _extract_inbound(payload: dict) -> tuple[str, str]:
    """Suporta payload Meta Cloud API e stub simples {text, from}."""
    if payload.get("text"):
        return str(payload.get("text") or "").strip(), str(payload.get("from") or "")
    try:
        entry = payload["entry"][0]
        change = entry["changes"][0]
        value = change["value"]
        msg = value["messages"][0]
        return str(msg.get("text", {}).get("body") or "").strip(), str(msg.get("from") or "")
    except (KeyError, IndexError, TypeError):
        return "", ""


def _send_outbound(to: str, text: str) -> None:
    mode = getattr(settings, "WHATSAPP_MODE", "mock").lower()
    if mode != "live":
        logger.info("whatsapp_outbound_mock", to=to, text=text[:200])
        return
    token = getattr(settings, "WHATSAPP_ACCESS_TOKEN", "") or ""
    phone_id = getattr(settings, "WHATSAPP_PHONE_NUMBER_ID", "") or ""
    if not token or not phone_id or not to:
        logger.warning("whatsapp_outbound_skipped")
        return
    # Live call omitted in stub — documentado no ADR; evita depender de rede no CI.
    logger.info("whatsapp_outbound_live_stub", to=to, phone_id=phone_id)
