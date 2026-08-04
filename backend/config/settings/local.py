"""Settings locais — DEBUG, SQLite ou Postgres via DATABASE_URL."""

from .base import *  # noqa: F401,F403
from .base import ALLOWED_HOSTS as BASE_ALLOWED_HOSTS
from .base import CSRF_TRUSTED_ORIGINS as BASE_CSRF_TRUSTED_ORIGINS
from .base import env

DEBUG = env.bool("DEBUG", default=True)
SECRET_KEY = env("SECRET_KEY", default="dev-only-change-me-techparts-f2")

# runserver em 0.0.0.0:8000 — Host do browser costuma ser localhost/127.0.0.1
_local_hosts = ("localhost", "127.0.0.1", "web")
ALLOWED_HOSTS = list(dict.fromkeys([*BASE_ALLOWED_HOSTS, *_local_hosts]))
_local_origins = (
    "http://localhost:8000",
    "http://127.0.0.1:8000",
)
CSRF_TRUSTED_ORIGINS = list(dict.fromkeys([*BASE_CSRF_TRUSTED_ORIGINS, *_local_origins]))

# Em local, Manifest static storage exige collectstatic; usar StaticFiles simples
STORAGES = {
    "default": {"BACKEND": "django.core.files.storage.FileSystemStorage"},
    "staticfiles": {
        "BACKEND": "django.contrib.staticfiles.storage.StaticFilesStorage",
    },
}

# Redis opcional: se REDIS_URL apontar para serviço real, usa django-redis
if env.bool("USE_REDIS_CACHE", default=False):
    CACHES = {
        "default": {
            "BACKEND": "django_redis.cache.RedisCache",
            "LOCATION": env("REDIS_URL"),
            "OPTIONS": {"CLIENT_CLASS": "django_redis.client.DefaultClient"},
        }
    }

EMAIL_BACKEND = "django.core.mail.backends.console.EmailBackend"
CELERY_TASK_ALWAYS_EAGER = env.bool("CELERY_TASK_ALWAYS_EAGER", default=True)
AXES_ENABLED = env.bool("AXES_ENABLED", default=False)
