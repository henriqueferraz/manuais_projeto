"""Settings de staging."""

import sentry_sdk
from sentry_sdk.integrations.celery import CeleryIntegration
from sentry_sdk.integrations.django import DjangoIntegration

from .base import *  # noqa: F401,F403
from .base import (
    AI_TOKEN_BUDGET_DAILY,
    ALLOWED_HOSTS,
    CSRF_TRUSTED_ORIGINS,
    SECRET_KEY,
    SENTRY_DSN,
    SENTRY_ENVIRONMENT,
    env,
)

DEBUG = False
SECURE_SSL_REDIRECT = env.bool("SECURE_SSL_REDIRECT", default=True)
SESSION_COOKIE_SECURE = True
CSRF_COOKIE_SECURE = True
SECURE_HSTS_SECONDS = 3600
SECURE_HSTS_INCLUDE_SUBDOMAINS = True
SECURE_PROXY_SSL_HEADER = ("HTTP_X_FORWARDED_PROTO", "https")

# Staging espelha produção com HSTS curto (T-P.2)
_INSECURE_SECRET_FRAGMENTS = ("change-me", "dev-only", "flower-local", "insecure")
if not SECRET_KEY or any(f in SECRET_KEY.lower() for f in _INSECURE_SECRET_FRAGMENTS):
    raise RuntimeError("SECRET_KEY forte e único é obrigatório em staging")
if not ALLOWED_HOSTS or ALLOWED_HOSTS == ["localhost", "127.0.0.1"]:
    raise RuntimeError("ALLOWED_HOSTS explícitos são obrigatórios em staging")
if SECURE_SSL_REDIRECT and not CSRF_TRUSTED_ORIGINS:
    raise RuntimeError("CSRF_TRUSTED_ORIGINS é obrigatório em staging com HTTPS")
_budget = int(AI_TOKEN_BUDGET_DAILY or 0)
if _budget <= 0:
    # Staging exige budget ativo (T-P.2); default 500k tokens/dia
    AI_TOKEN_BUDGET_DAILY = 500_000

AXES_ENABLED = env.bool("AXES_ENABLED", default=True)
MANUAL_CLAMAV_ENABLED = env.bool("MANUAL_CLAMAV_ENABLED", default=True)
MANUAL_AV_STUB_OK = env.bool("MANUAL_AV_STUB_OK", default=False)

CACHES = {
    "default": {
        "BACKEND": "django_redis.cache.RedisCache",
        "LOCATION": env("REDIS_URL"),
        "OPTIONS": {"CLIENT_CLASS": "django_redis.client.DefaultClient"},
    }
}

if SENTRY_DSN:
    sentry_sdk.init(
        dsn=SENTRY_DSN,
        environment=SENTRY_ENVIRONMENT or "staging",
        integrations=[DjangoIntegration(), CeleryIntegration()],
        traces_sample_rate=0.2,
        send_default_pii=False,
    )
