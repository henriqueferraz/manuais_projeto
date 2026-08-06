"""Rate limit para endpoints de IA (por IP e, se autenticado, por usuário)."""

from __future__ import annotations

from functools import wraps

from django.conf import settings
from django.core.cache import cache
from django.http import JsonResponse


def ai_rate_limit(view):
    """Rate limit configurável via AI_RATE_LIMIT (ex.: 30/m)."""

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
        cache.set(key, current + 1, timeout=window)
        return view(request, *args, **kwargs)

    return _wrapped
