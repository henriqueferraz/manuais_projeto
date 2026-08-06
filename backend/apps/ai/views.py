"""Views do chat RAG, diagnóstico e busca por foto (F5–F6)."""

from __future__ import annotations

import json
import uuid

import structlog
from django.http import HttpRequest, HttpResponse, JsonResponse, StreamingHttpResponse
from django.shortcuts import get_object_or_404, render
from django.views.decorators.http import require_GET, require_http_methods, require_POST

from apps.ai.models import ChatMessage, ChatSession, PhotoSearch
from apps.ai.services.chat import answer_question, format_sse
from apps.ai.services.diagnosis import diagnose_question
from apps.ai.services.escalate import register_feedback
from apps.ai.services.photo_search import create_photo_search
from apps.core.ratelimit import ai_rate_limit
from apps.products.models import Product

logger = structlog.get_logger(__name__)

SESSION_COOKIE = "tp_chat_key"

_DIAGNOSIS_HINTS = (
    "barulho",
    "ruído",
    "ruido",
    "não liga",
    "nao liga",
    "não gira",
    "nao gira",
    "vibra",
    "capacitor",
    "diagnóstico",
    "diagnostico",
    "sintoma",
    "quebra",
    "parou",
    "esquenta",
    "cheiro",
)


def _anonymous_key(request: HttpRequest) -> str:
    key = request.session.get(SESSION_COOKIE) or request.COOKIES.get(SESSION_COOKIE)
    if not key:
        key = uuid.uuid4().hex
        request.session[SESSION_COOKIE] = key
    return key


def _get_or_create_session(
    request: HttpRequest,
    *,
    session_id: str | None = None,
    product_id: int | None = None,
    category_id: int | None = None,
) -> ChatSession:
    user = request.user if request.user.is_authenticated else None
    anon = _anonymous_key(request)

    if session_id:
        qs = ChatSession.objects.all()
        if user:
            session = get_object_or_404(qs, pk=session_id, user=user)
        else:
            session = get_object_or_404(qs, pk=session_id, anonymous_key=anon)
        return session

    product = None
    category = None
    if product_id:
        product = Product.objects.filter(pk=product_id).select_related("category").first()
        if product:
            category = product.category
    elif category_id:
        from apps.catalog.models import Category

        category = Category.objects.filter(pk=category_id).first()

    return ChatSession.objects.create(
        user=user,
        anonymous_key="" if user else anon,
        product=product,
        category=category,
        request_id=getattr(request, "request_id", ""),
    )


def _wants_diagnosis(question: str, mode: str | None) -> bool:
    if mode == "diagnosis":
        return True
    if mode == "chat":
        return False
    q = question.lower()
    return any(h in q for h in _DIAGNOSIS_HINTS)


@require_GET
def chat_page(request: HttpRequest) -> HttpResponse:
    product_id = request.GET.get("produto") or request.GET.get("product")
    product = None
    if product_id and str(product_id).isdigit():
        product = Product.objects.filter(pk=int(product_id)).first()
    return render(
        request,
        "ai/chat.html",
        {
            "product": product,
            "page_title": "Assistente de diagnóstico",
        },
    )


@ai_rate_limit
@require_POST
def chat_stream(request: HttpRequest) -> HttpResponse:
    try:
        payload = json.loads(request.body.decode("utf-8") or "{}")
    except json.JSONDecodeError:
        return JsonResponse({"detail": "JSON inválido."}, status=400)

    question = (payload.get("question") or "").strip()
    if not question:
        return JsonResponse({"detail": "Informe a pergunta."}, status=400)

    session_id = payload.get("session_id")
    product_id = payload.get("product_id")
    category_id = payload.get("category_id")
    mode = (payload.get("mode") or "").strip().lower() or None
    try:
        session = _get_or_create_session(
            request,
            session_id=session_id,
            product_id=int(product_id) if product_id else None,
            category_id=int(category_id) if category_id else None,
        )
    except (TypeError, ValueError):
        return JsonResponse({"detail": "Filtros inválidos."}, status=400)

    request_id = getattr(request, "request_id", "") or ""
    use_diagnosis = _wants_diagnosis(question, mode)
    diagnosis_meta: dict = {}
    try:
        if use_diagnosis:
            user_id = request.user.pk if request.user.is_authenticated else None
            assistant, token_stream, diagnosis_meta = diagnose_question(
                session,
                question,
                request_id=request_id,
                user_id=user_id,
            )
        else:
            assistant, token_stream = answer_question(
                session,
                question,
                request_id=request_id,
            )
    except ValueError as exc:
        return JsonResponse({"detail": str(exc)}, status=400)

    def event_stream():
        meta = {
            "session_id": str(session.pk),
            "message_id": str(assistant.pk),
            "request_id": request_id,
            "sources": assistant.sources,
            "found_in_manual": assistant.found_in_manual,
            "confidence": assistant.confidence,
            "mode": "diagnosis" if use_diagnosis else "chat",
            "diagnosis_card": assistant.diagnosis_card or None,
        }
        meta.update({k: v for k, v in diagnosis_meta.items() if k not in meta})
        yield format_sse("meta", meta)
        for piece in token_stream:
            yield format_sse("token", {"text": piece})
        assistant.refresh_from_db()
        yield format_sse(
            "done",
            {
                "message_id": str(assistant.pk),
                "content": assistant.content,
                "sources": assistant.sources,
                "found_in_manual": assistant.found_in_manual,
                "confidence": assistant.confidence,
                "cost_estimate": float(assistant.cost_estimate),
                "latency_ms": assistant.latency_ms,
                "langsmith_trace_id": assistant.langsmith_trace_id,
                "request_id": request_id,
                "mode": "diagnosis" if use_diagnosis else "chat",
                "diagnosis_card": assistant.diagnosis_card or None,
                "recommended_skus": (assistant.diagnosis_card or {}).get("recommendedSkus") or [],
            },
        )

    response = StreamingHttpResponse(event_stream(), content_type="text/event-stream")
    response["Cache-Control"] = "no-cache"
    response["X-Accel-Buffering"] = "no"
    response["X-Request-ID"] = request_id
    if assistant.langsmith_trace_id:
        response["X-LangSmith-Trace"] = assistant.langsmith_trace_id
    return response


@ai_rate_limit
@require_http_methods(["POST"])
def chat_feedback(request: HttpRequest) -> JsonResponse:
    try:
        payload = json.loads(request.body.decode("utf-8") or "{}")
    except json.JSONDecodeError:
        return JsonResponse({"detail": "JSON inválido."}, status=400)

    message_id = payload.get("message_id")
    vote = payload.get("vote")
    reason = (payload.get("reason") or "").strip()
    email = (payload.get("email") or "").strip()
    if vote not in {"up", "down"}:
        return JsonResponse({"detail": "vote deve ser up ou down."}, status=400)

    message = get_object_or_404(ChatMessage, pk=message_id, role=ChatMessage.Role.ASSISTANT)
    session = message.session
    if request.user.is_authenticated:
        if session.user_id and session.user_id != request.user.id:
            return JsonResponse({"detail": "Não autorizado."}, status=403)
    else:
        anon = _anonymous_key(request)
        if session.anonymous_key and session.anonymous_key != anon:
            return JsonResponse({"detail": "Não autorizado."}, status=403)

    feedback = register_feedback(
        message,
        vote=vote,
        reason=reason,
        email=email,
        user=request.user if request.user.is_authenticated else None,
    )
    ticket_code = feedback.created_ticket.code if feedback.created_ticket_id else None
    return JsonResponse(
        {
            "ok": True,
            "vote": feedback.vote,
            "ticket_code": ticket_code,
            "consecutive_downvotes": session.consecutive_downvotes,
        }
    )


@ai_rate_limit
@require_POST
def photo_upload(request: HttpRequest) -> HttpResponse:
    upload = request.FILES.get("photo") or request.FILES.get("image")
    if not upload:
        return JsonResponse({"detail": "Envie o campo photo."}, status=400)

    product_id = request.POST.get("product_id") or None
    try:
        pid = int(product_id) if product_id else None
    except (TypeError, ValueError):
        return JsonResponse({"detail": "product_id inválido."}, status=400)

    try:
        search = create_photo_search(
            content=upload.read(),
            filename=getattr(upload, "name", "photo.jpg"),
            user=request.user if request.user.is_authenticated else None,
            anonymous_key=_anonymous_key(request),
            product_id=pid,
            enqueue=True,
        )
    except Exception as exc:  # ValidationError etc.
        from django.core.exceptions import ValidationError

        if isinstance(exc, ValidationError):
            msg = "; ".join(exc.messages) if hasattr(exc, "messages") else str(exc)
            return JsonResponse({"detail": msg}, status=400)
        raise

    # Em Celery eager o resultado já está pronto
    search.refresh_from_db()
    if request.headers.get("HX-Request"):
        return render(
            request,
            "ai/partials/photo_candidates.html",
            {"search": search},
        )
    return JsonResponse(
        {
            "id": str(search.pk),
            "status": search.status,
            "candidates": search.candidates,
            "error": search.error_message,
            "latency_ms": search.latency_ms,
        }
    )


@require_GET
def photo_status(request: HttpRequest, search_id: uuid.UUID) -> HttpResponse:
    search = get_object_or_404(PhotoSearch, pk=search_id)
    if request.user.is_authenticated:
        if search.user_id and search.user_id != request.user.id:
            return JsonResponse({"detail": "Não autorizado."}, status=403)
    else:
        anon = _anonymous_key(request)
        if search.anonymous_key and search.anonymous_key != anon:
            return JsonResponse({"detail": "Não autorizado."}, status=403)

    if request.headers.get("HX-Request") or request.GET.get("partial"):
        return render(
            request,
            "ai/partials/photo_candidates.html",
            {"search": search},
        )
    return JsonResponse(
        {
            "id": str(search.pk),
            "status": search.status,
            "candidates": search.candidates,
            "error": search.error_message,
            "latency_ms": search.latency_ms,
        }
    )
