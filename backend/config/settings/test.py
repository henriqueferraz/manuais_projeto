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
MANUAL_AV_STUB_OK = True
MANUAL_CLAMAV_ENABLED = False
USE_R2_STORAGE = False
PAYMENT_PROVIDER = "mock"
NFE_PROVIDER = "mock"
CELERY_TASK_ALWAYS_EAGER = True

STORAGES = {
    "default": {"BACKEND": "django.core.files.storage.InMemoryStorage"},
    "staticfiles": {
        "BACKEND": "django.contrib.staticfiles.storage.StaticFilesStorage",
    },
}
