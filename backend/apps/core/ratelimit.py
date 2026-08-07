"""Rate limit para endpoints de IA (por IP e, se autenticado, por usuário)."""

from __future__ import annotations

from functools import wraps

from django.conf import settings
from django.core.cache import cache
from django.http import JsonResponse


def ai_rate_limit(view):
    """Rate limit configurável via AI_RATE_LIMIT (ex.: 30/m) + budget diário de tokens."""

    @wraps(view)
    def _wrapped(request, *args, **kwargs):
        limit = getattr(settings, "AI_RATE_LIMIT", "30/m")
        try:
            count_str, period = limit.split("/")
            max_count = int(count_str)
            window = {"s": 1, "m": 60, "h": 3600}.get(period, 60)
        except (ValueError, AttributeError):
            max_count, window = 30, 60

        ip = request.META.get("REMOTE_ADDR", "unknown")
        user = getattr(request, "user", None)
        authenticated = user is not None and getattr(user, "is_authenticated", False)
        user_part = f"u{user.pk}" if authenticated else "anon"
        key = f"ai-rate:{user_part}:{ip}"
        current = cache.get(key, 0)
        if current >= max_count:
            return JsonResponse(
                {"detail": "Rate limit excedido. Tente novamente em breve."},
                status=429,
            )

        daily_budget = int(getattr(settings, "AI_TOKEN_BUDGET_DAILY", 0) or 0)
        if daily_budget > 0:
            day_key = "ai-token-budget:daily"
            used = int(cache.get(day_key, 0) or 0)
            if used >= daily_budget:
                return JsonResponse(
                    {"detail": "Orçamento diário de tokens de IA esgotado."},
                    status=429,
                )

        per_req = int(getattr(settings, "AI_TOKEN_BUDGET_PER_REQUEST", 0) or 0)
        if per_req > 0:
            # Guardrail: budget por request; uso real via record_token_usage.
            request._ai_token_budget_per_request = per_req  # noqa: SLF001

        cache.set(key, current + 1, timeout=window)
        return view(request, *args, **kwargs)

    return _wrapped


def record_token_usage(tokens: int) -> None:
    """Incrementa contador diário de tokens (F8 / ADR-0008)."""
    if tokens <= 0:
        return
    day_key = "ai-token-budget:daily"
    used = int(cache.get(day_key, 0) or 0)
    new_used = used + int(tokens)
    cache.set(day_key, new_used, timeout=86400)

    daily_budget = int(getattr(settings, "AI_TOKEN_BUDGET_DAILY", 0) or 0)
    if daily_budget > 0 and new_used >= daily_budget:
        # Alerta único por dia (cache flag) — T-P.2
        flag_key = "ai-token-budget:alerted"
        if not cache.get(flag_key):
            cache.set(flag_key, 1, timeout=86400)
            try:
                from apps.dashboard.models import OpsAlert
                from apps.dashboard.services.monitoring import raise_ops_alert

                raise_ops_alert(
                    kind=OpsAlert.Kind.COST,
                    severity=OpsAlert.Severity.CRITICAL,
                    title="Orçamento diário de tokens esgotado",
                    message=(
                        f"Uso de tokens ({new_used}) atingiu o budget diário "
                        f"({daily_budget}). Novas requisições de IA retornam 429."
                    ),
                    payload={"used": new_used, "budget": daily_budget},
                )
            except Exception as exc:  # noqa: BLE001
                import structlog

                structlog.get_logger(__name__).warning(
                    "token_budget_alert_failed",
                    error=str(exc)[:200],
                )
