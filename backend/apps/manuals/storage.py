"""Storage R2 (S3-compatible) e URLs assinadas."""

from __future__ import annotations

from datetime import timedelta
from typing import Any

from django.conf import settings
from django.core.files.storage import Storage, default_storage
from django.utils.module_loading import import_string


def use_r2() -> bool:
    return bool(getattr(settings, "USE_R2_STORAGE", False))


def get_manual_storage() -> Storage:
    """Storage de manuais: R2 quando configurado, senão default (FS/InMemory)."""
    backend = getattr(settings, "MANUAL_STORAGE_BACKEND", None)
    if backend:
        return import_string(backend)()
    return default_storage


def signed_url(storage_key: str, *, expires_seconds: int | None = None) -> str:
    """
    Gera URL assinada para download privado.
    Em filesystem local, devolve URL de media.
    """
    if not storage_key:
        return ""
    expires = expires_seconds or int(getattr(settings, "MANUAL_SIGNED_URL_EXPIRES", 3600))
    storage = get_manual_storage()

    if hasattr(storage, "url"):
        # S3Boto3Storage: querystring_auth=True gera URL assinada
        try:
            if hasattr(storage, "bucket"):
                return storage.url(storage_key, expire=expires)  # type: ignore[call-arg]
        except TypeError:
            pass
        try:
            return storage.url(storage_key)
        except Exception:  # noqa: BLE001
            return ""
    return ""


def r2_settings_dict() -> dict[str, Any]:
    """Parâmetros do storage Cloudflare R2 (API S3-compatible)."""
    return {
        "access_key": getattr(settings, "R2_ACCESS_KEY_ID", ""),
        "secret_key": getattr(settings, "R2_SECRET_ACCESS_KEY", ""),
        "bucket_name": getattr(settings, "R2_BUCKET_NAME", ""),
        "endpoint_url": getattr(settings, "R2_ENDPOINT_URL", ""),
        "region_name": getattr(settings, "R2_REGION_NAME", "auto"),
        "default_acl": "private",
        "querystring_auth": True,
        "querystring_expire": int(getattr(settings, "MANUAL_SIGNED_URL_EXPIRES", 3600)),
        "file_overwrite": False,
        "object_parameters": {"CacheControl": "max-age=86400"},
    }


def signed_url_expires_delta() -> timedelta:
    return timedelta(seconds=int(getattr(settings, "MANUAL_SIGNED_URL_EXPIRES", 3600)))
