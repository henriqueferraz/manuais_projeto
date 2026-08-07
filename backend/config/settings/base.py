"""Settings compartilhados (local / staging / production)."""

from pathlib import Path

import environ
import structlog
from apps.core.logging import mask_pii

BASE_DIR = Path(__file__).resolve().parent.parent.parent
REPO_ROOT = BASE_DIR.parent

env = environ.Env(
    DEBUG=(bool, False),
    ALLOWED_HOSTS=(list, ["localhost", "127.0.0.1"]),
    CSRF_TRUSTED_ORIGINS=(list, []),
    DATABASE_URL=(str, f"sqlite:///{BASE_DIR / 'db.sqlite3'}"),
    REDIS_URL=(str, "redis://127.0.0.1:6379/0"),
    CELERY_BROKER_URL=(str, "redis://127.0.0.1:6379/1"),
    SENTRY_DSN=(str, ""),
    SENTRY_ENVIRONMENT=(str, "local"),
    SECURE_SSL_REDIRECT=(bool, False),
    SESSION_COOKIE_SECURE=(bool, False),
    CSRF_COOKIE_SECURE=(bool, False),
    AXES_ENABLED=(bool, True),
    AI_RATE_LIMIT=(str, "30/m"),
    AI_TOKEN_BUDGET_DAILY=(int, 0),
    AI_TOKEN_BUDGET_PER_REQUEST=(int, 0),
    WHATSAPP_MODE=(str, "mock"),
    WHATSAPP_VERIFY_TOKEN=(str, "techparts-dev"),
    WHATSAPP_APP_SECRET=(str, ""),
    WHATSAPP_ACCESS_TOKEN=(str, ""),
    WHATSAPP_PHONE_NUMBER_ID=(str, ""),
    PWA_ENABLED=(bool, False),
    DATABASE_READ_REPLICA_URL=(str, ""),
    USE_R2_STORAGE=(bool, False),
    MANUAL_MAX_UPLOAD_BYTES=(int, 25 * 1024 * 1024),
    MANUAL_SIGNED_URL_EXPIRES=(int, 3600),
    MANUAL_CLAMAV_ENABLED=(bool, False),
    MANUAL_AV_STUB_OK=(bool, True),
    CLAMAV_HOST=(str, ""),
    CLAMAV_PORT=(int, 3310),
    MANUAL_OCR_ENABLED=(bool, False),
    EXTRACTION_LLM_MODE=(str, "mock"),
    ANTHROPIC_API_KEY=(str, ""),
    ANTHROPIC_MODEL=(str, "claude-sonnet-4-5-20250929"),
    LANGSMITH_TRACING=(bool, False),
    LANGSMITH_API_KEY=(str, ""),
    LANGSMITH_PROJECT=(str, "techparts-ai"),
    CHAT_LLM_MODE=(str, "mock"),
    EMBEDDING_MODE=(str, "mock"),
    EMBEDDING_DIMS=(int, 64),
    OPENAI_API_KEY=(str, ""),
    OPENAI_EMBEDDING_MODEL=(str, "text-embedding-3-small"),
    RAG_CHUNK_SIZE=(int, 900),
    RAG_CHUNK_OVERLAP=(int, 120),
    RAG_TOP_K=(int, 4),
    RAG_MIN_SCORE=(float, 0.12),
    USE_PGVECTOR=(bool, True),
    AI_COST_ALERT_USD=(float, 5.0),
    AI_LATENCY_ALERT_MS=(int, 8000),
    PHOTO_MAX_UPLOAD_BYTES=(int, 5 * 1024 * 1024),
    PHOTO_LLM_MODE=(str, "mock"),
    DIAGNOSIS_LLM_MODE=(str, "mock"),
    GOLDEN_MIN_SCORE=(float, 0.66),
    RAG_GOLDEN_MIN_SCORE=(float, 0.66),
    FLOWER_URL=(str, "http://localhost:5555"),
    SENTRY_UI_URL=(str, ""),
    GRAFANA_URL=(str, ""),
    SLACK_WEBHOOK_URL=(str, ""),
    OPS_ALERT_EMAILS=(list, []),
)

environ.Env.read_env(REPO_ROOT / ".env")

SECRET_KEY = env("SECRET_KEY", default="change-me-in-production-use-env")
DEBUG = env("DEBUG")
ALLOWED_HOSTS = env("ALLOWED_HOSTS")
CSRF_TRUSTED_ORIGINS = env("CSRF_TRUSTED_ORIGINS")

DJANGO_APPS = [
    "django.contrib.admin",
    "django.contrib.auth",
    "django.contrib.contenttypes",
    "django.contrib.sessions",
    "django.contrib.messages",
    "django.contrib.staticfiles",
]

THIRD_PARTY_APPS = [
    "rest_framework",
    "django_otp",
    "django_otp.plugins.otp_totp",
    "django_otp.plugins.otp_static",
    "two_factor",
    "axes",
    "simple_history",
    "django_structlog",
    "csp",
]

LOCAL_APPS = [
    "apps.core.apps.CoreConfig",
    "apps.accounts.apps.AccountsConfig",
    "apps.catalog.apps.CatalogConfig",
    "apps.products.apps.ProductsConfig",
    "apps.cart.apps.CartConfig",
    "apps.checkout.apps.CheckoutConfig",
    "apps.orders.apps.OrdersConfig",
    "apps.tickets.apps.TicketsConfig",
    "apps.ai.apps.AiConfig",
    "apps.manuals.apps.ManualsConfig",
    "apps.compatibility.apps.CompatibilityConfig",
    "apps.dashboard.apps.DashboardConfig",
    "apps.notifications.apps.NotificationsConfig",
    "apps.subscriptions.apps.SubscriptionsConfig",
    "apps.partners.apps.PartnersConfig",
    "apps.channels.apps.ChannelsConfig",
    "apps.warranty.apps.WarrantyConfig",
]

INSTALLED_APPS = DJANGO_APPS + THIRD_PARTY_APPS + LOCAL_APPS

MIDDLEWARE = [
    "django.middleware.security.SecurityMiddleware",
    "whitenoise.middleware.WhiteNoiseMiddleware",
    "django.contrib.sessions.middleware.SessionMiddleware",
    "django.middleware.common.CommonMiddleware",
    "django.middleware.csrf.CsrfViewMiddleware",
    "django.contrib.auth.middleware.AuthenticationMiddleware",
    "django_otp.middleware.OTPMiddleware",
    "django.contrib.messages.middleware.MessageMiddleware",
    "django.middleware.clickjacking.XFrameOptionsMiddleware",
    "csp.middleware.CSPMiddleware",
    "simple_history.middleware.HistoryRequestMiddleware",
    "axes.middleware.AxesMiddleware",
    "django_structlog.middlewares.RequestMiddleware",
    "apps.core.middleware.RequestIdMiddleware",
]

ROOT_URLCONF = "config.urls"
WSGI_APPLICATION = "config.wsgi.application"
ASGI_APPLICATION = "config.asgi.application"

TEMPLATES = [
    {
        "BACKEND": "django.template.backends.django.DjangoTemplates",
        "DIRS": [BASE_DIR / "templates"],
        "APP_DIRS": True,
        "OPTIONS": {
            "context_processors": [
                "django.template.context_processors.request",
                "django.template.context_processors.debug",
                "django.contrib.auth.context_processors.auth",
                "django.contrib.messages.context_processors.messages",
                "apps.core.context_processors.brand",
            ],
        },
    },
]

DATABASES = {"default": env.db("DATABASE_URL")}

CACHES = {
    "default": {
        "BACKEND": "django.core.cache.backends.locmem.LocMemCache",
        "LOCATION": "techparts-local",
    }
}

REDIS_URL = env("REDIS_URL")
CELERY_BROKER_URL = env("CELERY_BROKER_URL")
CELERY_RESULT_BACKEND = env("CELERY_BROKER_URL")
CELERY_ACCEPT_CONTENT = ["json"]
CELERY_TASK_SERIALIZER = "json"
CELERY_RESULT_SERIALIZER = "json"
CELERY_TIMEZONE = "America/Sao_Paulo"
CELERY_TASK_ALWAYS_EAGER = env.bool("CELERY_TASK_ALWAYS_EAGER", default=False)

AUTH_PASSWORD_VALIDATORS = [
    {"NAME": "django.contrib.auth.password_validation.UserAttributeSimilarityValidator"},
    {"NAME": "django.contrib.auth.password_validation.MinimumLengthValidator"},
    {"NAME": "django.contrib.auth.password_validation.CommonPasswordValidator"},
    {"NAME": "django.contrib.auth.password_validation.NumericPasswordValidator"},
]

LANGUAGE_CODE = "pt-br"
TIME_ZONE = "America/Sao_Paulo"
USE_I18N = True
USE_TZ = True

STATIC_URL = "/static/"
STATIC_ROOT = BASE_DIR / "staticfiles"
STATICFILES_DIRS = [BASE_DIR / "static"]
STORAGES = {
    "default": {"BACKEND": "django.core.files.storage.FileSystemStorage"},
    "staticfiles": {
        "BACKEND": "whitenoise.storage.CompressedManifestStaticFilesStorage",
    },
}

MEDIA_URL = "/media/"
MEDIA_ROOT = BASE_DIR / "media"

DEFAULT_AUTO_FIELD = "django.db.models.BigAutoField"

LOGIN_URL = "two_factor:login"
LOGIN_REDIRECT_URL = "/"
LOGOUT_REDIRECT_URL = "/"

# --- Segurança ---
SECURE_SSL_REDIRECT = env("SECURE_SSL_REDIRECT")
SESSION_COOKIE_SECURE = env("SESSION_COOKIE_SECURE")
CSRF_COOKIE_SECURE = env("CSRF_COOKIE_SECURE")
SESSION_COOKIE_HTTPONLY = True
CSRF_COOKIE_HTTPONLY = True
SESSION_COOKIE_SAMESITE = "Lax"
CSRF_COOKIE_SAMESITE = "Lax"
SECURE_CONTENT_TYPE_NOSNIFF = True
SECURE_REFERRER_POLICY = "same-origin"
X_FRAME_OPTIONS = "DENY"
SECURE_BROWSER_XSS_FILTER = True

CONTENT_SECURITY_POLICY = {
    "DIRECTIVES": {
        "default-src": ("'self'",),
        "script-src": ("'self'",),
        "style-src": ("'self'", "https://fonts.googleapis.com"),
        "font-src": ("'self'", "https://fonts.gstatic.com", "data:"),
        "img-src": ("'self'", "data:", "https:"),
        "connect-src": ("'self'",),
        "frame-ancestors": ("'none'",),
        "base-uri": ("'self'",),
        "form-action": ("'self'",),
    }
}

# --- Auth / 2FA / Axes ---
AUTHENTICATION_BACKENDS = [
    "axes.backends.AxesStandaloneBackend",
    "django.contrib.auth.backends.ModelBackend",
]
AXES_ENABLED = env("AXES_ENABLED")
AXES_FAILURE_LIMIT = 5
AXES_COOLOFF_TIME = 1  # hours
AXES_LOCKOUT_PARAMETERS = [["username", "ip_address"]]
AXES_RESET_ON_SUCCESS = True

TWO_FACTOR_PATCH_ADMIN = True
OTP_TOTP_ISSUER = "TechParts AI"

# Grupos RBAC iniciais (criados via management command)
RBAC_GROUPS = (
    "admin",
    "revisao_catalogo",
    "suporte",
)

# Rate limit stub para endpoints de IA (F5+)
AI_RATE_LIMIT = env("AI_RATE_LIMIT")
AI_TOKEN_BUDGET_DAILY = env("AI_TOKEN_BUDGET_DAILY")
AI_TOKEN_BUDGET_PER_REQUEST = env("AI_TOKEN_BUDGET_PER_REQUEST")

# --- F8: canais / PWA / escala ---
WHATSAPP_MODE = env("WHATSAPP_MODE")
WHATSAPP_VERIFY_TOKEN = env("WHATSAPP_VERIFY_TOKEN")
WHATSAPP_APP_SECRET = env("WHATSAPP_APP_SECRET")
WHATSAPP_ACCESS_TOKEN = env("WHATSAPP_ACCESS_TOKEN")
WHATSAPP_PHONE_NUMBER_ID = env("WHATSAPP_PHONE_NUMBER_ID")
PWA_ENABLED = env("PWA_ENABLED")
DATABASE_READ_REPLICA_URL = env("DATABASE_READ_REPLICA_URL")

# --- F3: manuais / R2 / extração ---
USE_R2_STORAGE = env("USE_R2_STORAGE")
MANUAL_MAX_UPLOAD_BYTES = env("MANUAL_MAX_UPLOAD_BYTES")
MANUAL_SIGNED_URL_EXPIRES = env("MANUAL_SIGNED_URL_EXPIRES")
MANUAL_ALLOWED_MIME_TYPES = {"application/pdf"}
MANUAL_CLAMAV_ENABLED = env("MANUAL_CLAMAV_ENABLED")
MANUAL_AV_STUB_OK = env("MANUAL_AV_STUB_OK")
CLAMAV_HOST = env("CLAMAV_HOST")
CLAMAV_PORT = env("CLAMAV_PORT")
MANUAL_OCR_ENABLED = env("MANUAL_OCR_ENABLED")
EXTRACTION_LLM_MODE = env("EXTRACTION_LLM_MODE")
ANTHROPIC_API_KEY = env("ANTHROPIC_API_KEY")
ANTHROPIC_MODEL = env("ANTHROPIC_MODEL")
LANGSMITH_TRACING = env("LANGSMITH_TRACING")
LANGSMITH_API_KEY = env("LANGSMITH_API_KEY")
LANGSMITH_PROJECT = env("LANGSMITH_PROJECT")
CART_RESERVATION_MINUTES = env.int("CART_RESERVATION_MINUTES", default=30)
CATALOG_CACHE_TTL = env.int("CATALOG_CACHE_TTL", default=60)

# --- F5: chat RAG ---
CHAT_LLM_MODE = env("CHAT_LLM_MODE")
EMBEDDING_MODE = env("EMBEDDING_MODE")
EMBEDDING_DIMS = env("EMBEDDING_DIMS")
OPENAI_API_KEY = env("OPENAI_API_KEY")
OPENAI_EMBEDDING_MODEL = env("OPENAI_EMBEDDING_MODEL")
RAG_CHUNK_SIZE = env("RAG_CHUNK_SIZE")
RAG_CHUNK_OVERLAP = env("RAG_CHUNK_OVERLAP")
RAG_TOP_K = env("RAG_TOP_K")
RAG_MIN_SCORE = env("RAG_MIN_SCORE")
USE_PGVECTOR = env("USE_PGVECTOR")
AI_COST_ALERT_USD = env("AI_COST_ALERT_USD")
AI_LATENCY_ALERT_MS = env("AI_LATENCY_ALERT_MS")
PHOTO_MAX_UPLOAD_BYTES = env("PHOTO_MAX_UPLOAD_BYTES")
PHOTO_LLM_MODE = env("PHOTO_LLM_MODE")
DIAGNOSIS_LLM_MODE = env("DIAGNOSIS_LLM_MODE")
GOLDEN_MIN_SCORE = env("GOLDEN_MIN_SCORE")
RAG_GOLDEN_MIN_SCORE = env("RAG_GOLDEN_MIN_SCORE")
FLOWER_URL = env("FLOWER_URL")
SENTRY_UI_URL = env("SENTRY_UI_URL")
GRAFANA_URL = env("GRAFANA_URL")
SLACK_WEBHOOK_URL = env("SLACK_WEBHOOK_URL")
OPS_ALERT_EMAILS = env("OPS_ALERT_EMAILS")

# --- F4b: checkout / pagamento / frete / NF-e ---
PAYMENT_PROVIDER = env("PAYMENT_PROVIDER", default="mock")
PAYMENT_WEBHOOK_SECRET = env("PAYMENT_WEBHOOK_SECRET", default="dev-webhook-secret")
STRIPE_SECRET_KEY = env("STRIPE_SECRET_KEY", default="")
STRIPE_WEBHOOK_SECRET = env("STRIPE_WEBHOOK_SECRET", default="")
MERCADOPAGO_ACCESS_TOKEN = env("MERCADOPAGO_ACCESS_TOKEN", default="")
MERCADOPAGO_WEBHOOK_SECRET = env("MERCADOPAGO_WEBHOOK_SECRET", default="")
MELHOR_ENVIO_ENABLED = env.bool("MELHOR_ENVIO_ENABLED", default=False)
MELHOR_ENVIO_TOKEN = env("MELHOR_ENVIO_TOKEN", default="")
SHIPPING_FIXED_PRICE = env("SHIPPING_FIXED_PRICE", default="19.90")
SHIPPING_FREE_FROM = env("SHIPPING_FREE_FROM", default="299.00")
NFE_PROVIDER = env("NFE_PROVIDER", default="mock")
FOCUSNFE_TOKEN = env("FOCUSNFE_TOKEN", default="")
FOCUSNFE_BASE_URL = env("FOCUSNFE_BASE_URL", default="https://homologacao.focusnfe.com.br")
NFE_EMITTER_CNPJ = env("NFE_EMITTER_CNPJ", default="")
NFE_DEFAULT_CFOP = env("NFE_DEFAULT_CFOP", default="5102")
DEFAULT_FROM_EMAIL = env("DEFAULT_FROM_EMAIL", default="noreply@techparts.local")
TICKET_SLA_HOURS = env.int("TICKET_SLA_HOURS", default=24)
RETURN_CDC_DAYS = env.int("RETURN_CDC_DAYS", default=7)
MELHOR_ENVIO_STUB = env.bool("MELHOR_ENVIO_STUB", default=False)
MELHOR_ENVIO_BASE_URL = env("MELHOR_ENVIO_BASE_URL", default="https://sandbox.melhorenvio.com.br")
MELHOR_ENVIO_FROM_CEP = env("MELHOR_ENVIO_FROM_CEP", default="01310100")
SUBSCRIPTION_BILLING_MODE = env("SUBSCRIPTION_BILLING_MODE", default="mock")
WHATSAPP_API_VERSION = env("WHATSAPP_API_VERSION", default="v21.0")

CELERY_BEAT_SCHEDULE = {
    "tickets-check-sla": {
        "task": "tickets.check_sla",
        "schedule": 15 * 60.0,  # segundos
    },
    "dashboard-scan-alerts": {
        "task": "dashboard.scan_alerts",
        "schedule": 10 * 60.0,
    },
}

AWS_ACCESS_KEY_ID = env("AWS_ACCESS_KEY_ID", default="")
AWS_SECRET_ACCESS_KEY = env("AWS_SECRET_ACCESS_KEY", default="")
AWS_STORAGE_BUCKET_NAME = env("AWS_STORAGE_BUCKET_NAME", default="")
AWS_S3_ENDPOINT_URL = env("AWS_S3_ENDPOINT_URL", default="")
AWS_S3_REGION_NAME = env("AWS_S3_REGION_NAME", default="auto")
AWS_DEFAULT_ACL = "private"
AWS_QUERYSTRING_AUTH = True
AWS_QUERYSTRING_EXPIRE = MANUAL_SIGNED_URL_EXPIRES
AWS_S3_FILE_OVERWRITE = False

if USE_R2_STORAGE:
    STORAGES = {
        "default": {
            "BACKEND": "storages.backends.s3boto3.S3Boto3Storage",
        },
        "staticfiles": {
            "BACKEND": "whitenoise.storage.CompressedManifestStaticFilesStorage",
        },
    }

# --- Observabilidade ---
SENTRY_DSN = env("SENTRY_DSN")
SENTRY_ENVIRONMENT = env("SENTRY_ENVIRONMENT")

LOGGING = {
    "version": 1,
    "disable_existing_loggers": False,
    "formatters": {
        "structlog": {
            "()": structlog.stdlib.ProcessorFormatter,
            "processor": structlog.dev.ConsoleRenderer(),
        },
    },
    "handlers": {
        "console": {
            "class": "logging.StreamHandler",
            "formatter": "structlog",
        },
    },
    "root": {
        "handlers": ["console"],
        "level": "INFO",
    },
}

structlog.configure(
    processors=[
        structlog.contextvars.merge_contextvars,
        structlog.stdlib.filter_by_level,
        structlog.processors.TimeStamper(fmt="iso"),
        structlog.stdlib.add_logger_name,
        structlog.stdlib.add_log_level,
        mask_pii,
        structlog.stdlib.PositionalArgumentsFormatter(),
        structlog.processors.StackInfoRenderer(),
        structlog.processors.format_exc_info,
        structlog.stdlib.ProcessorFormatter.wrap_for_formatter,
    ],
    logger_factory=structlog.stdlib.LoggerFactory(),
    wrapper_class=structlog.stdlib.BoundLogger,
    cache_logger_on_first_use=True,
)

REST_FRAMEWORK = {
    "DEFAULT_AUTHENTICATION_CLASSES": [
        "rest_framework.authentication.SessionAuthentication",
    ],
    "DEFAULT_PERMISSION_CLASSES": [
        "rest_framework.permissions.IsAuthenticated",
    ],
    "DEFAULT_THROTTLE_RATES": {
        "ai": AI_RATE_LIMIT,
    },
}
