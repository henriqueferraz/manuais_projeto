"""Settings de produção."""

import sentry_sdk
from sentry_sdk.integrations.celery import CeleryIntegration
from sentry_sdk.integrations.django import DjangoIntegration

from .base import *  # noqa: F401,F403
from .base import (
    AI_TOKEN_BUDGET_DAILY,
    ALLOWED_HOSTS,
    AXES_ENABLED,
    CSRF_TRUSTED_ORIGINS,
    SECRET_KEY,
    SENTRY_DSN,
    SENTRY_ENVIRONMENT,
    env,
)

DEBUG = False
SECURE_SSL_REDIRECT = True
SESSION_COOKIE_SECURE = True
CSRF_COOKIE_SECURE = True
SECURE_HSTS_SECONDS = 31536000
SECURE_HSTS_INCLUDE_SUBDOMAINS = True
SECURE_HSTS_PRELOAD = True
SECURE_PROXY_SSL_HEADER = ("HTTP_X_FORWARDED_PROTO", "https")

# Hardening obrigatório (T-P.2 / docs/security-hardening.md)
_INSECURE_SECRET_FRAGMENTS = (
    "change-me",
    "dev-only",
    "flower-local",
    "insecure",
)
if not SECRET_KEY or any(f in SECRET_KEY.lower() for f in _INSECURE_SECRET_FRAGMENTS):
    raise RuntimeError("SECRET_KEY forte e único é obrigatório em produção")
if len(SECRET_KEY) < 50:
    raise RuntimeError("SECRET_KEY deve ter ao menos 50 caracteres em produção")
if not ALLOWED_HOSTS or ALLOWED_HOSTS == ["localhost", "127.0.0.1"]:
    raise RuntimeError("ALLOWED_HOSTS explícitos são obrigatórios em produção")
if not CSRF_TRUSTED_ORIGINS:
    raise RuntimeError("CSRF_TRUSTED_ORIGINS é obrigatório em produção (HTTPS)")
if not AXES_ENABLED:
    raise RuntimeError("AXES_ENABLED=true é obrigatório em produção")
if int(AI_TOKEN_BUDGET_DAILY or 0) <= 0:
    raise RuntimeError("AI_TOKEN_BUDGET_DAILY > 0 é obrigatório em produção (custo)")

# Uploads: preferir ClamAV em produção (pode ser desligado só com justificativa ops)
MANUAL_CLAMAV_ENABLED = env.bool("MANUAL_CLAMAV_ENABLED", default=True)
MANUAL_AV_STUB_OK = False

CACHES = {
    "default": {
        "BACKEND": "django_redis.cache.RedisCache",
        "LOCATION": env("REDIS_URL"),
        "OPTIONS": {"CLIENT_CLASS": "django_redis.client.DefaultClient"},
    }
}

if not SENTRY_DSN:
    raise RuntimeError("SENTRY_DSN é obrigatório em produção")

sentry_sdk.init(
    dsn=SENTRY_DSN,
    environment=SENTRY_ENVIRONMENT or "production",
    integrations=[DjangoIntegration(), CeleryIntegration()],
    traces_sample_rate=0.1,
    send_default_pii=False,
)
