"""Settings para E2E Playwright (SQLite em arquivo — compartilhado com live_server)."""

from django.db.backends.signals import connection_created

from .base import BASE_DIR
from .test import *  # noqa: F401,F403

DEBUG = True  # servir static em live_server
ALLOWED_HOSTS = ["testserver", "localhost", "127.0.0.1"]

DATABASES = {
    "default": {
        "ENGINE": "django.db.backends.sqlite3",
        "NAME": str(BASE_DIR / "e2e.sqlite3"),
        "OPTIONS": {"timeout": 60},
    }
}


def _enable_sqlite_wal(sender, connection, **kwargs):
    if connection.vendor == "sqlite":
        cursor = connection.cursor()
        cursor.execute("PRAGMA journal_mode=WAL;")
        cursor.execute("PRAGMA busy_timeout=60000;")


connection_created.connect(_enable_sqlite_wal)
