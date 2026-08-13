"""Settings de CI/pytest — SQLite em memória, eager Celery, Axes off."""

from .base import *  # noqa: F401,F403

DEBUG = False
SECRET_KEY = "ci-test-secret-key-not-for-production"  # nosec B105
ALLOWED_HOSTS = ["testserver", "localhost", "127.0.0.1"]

DATABASES = {
    "default": {
        "ENGINE": "django.db.backends.sqlite3",
        "NAME": ":memory:",
    }
}

PASSWORD_HASHERS = ["django.contrib.auth.hashers.MD5PasswordHasher"]
CELERY_TASK_ALWAYS_EAGER = True
AXES_ENABLED = False
EMAIL_BACKEND = "django.core.mail.backends.locmem.EmailBackend"
EXTRACTION_LLM_MODE = "mock"
CHAT_LLM_MODE = "mock"
CHAT_MIN_ANSWER_CONFIDENCE = 0.70
EMBEDDING_MODE = "mock"
EMBEDDING_DIMS = 64
USE_PGVECTOR = False
MANUAL_AV_STUB_OK = True
MANUAL_CLAMAV_ENABLED = False
USE_R2_STORAGE = False
PAYMENT_PROVIDER = "mock"
SUBSCRIPTION_BILLING_MODE = "mock"
NFE_PROVIDER = "mock"
MELHOR_ENVIO_ENABLED = False
MELHOR_ENVIO_STUB = False
CELERY_TASK_ALWAYS_EAGER = True
AI_RATE_LIMIT = "100/m"
PHOTO_LLM_MODE = "mock"
WEB_IMAGE_SEARCH_MODE = "mock"
DIAGNOSIS_LLM_MODE = "mock"
PHOTO_MAX_UPLOAD_BYTES = 5 * 1024 * 1024

STORAGES = {
    "default": {"BACKEND": "django.core.files.storage.InMemoryStorage"},
    "staticfiles": {
        "BACKEND": "django.contrib.staticfiles.storage.StaticFilesStorage",
    },
}
