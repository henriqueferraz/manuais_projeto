"""Assets de marca (hero/bento) no Cloudflare R2."""

from __future__ import annotations

from apps.manuals.storage import signed_url, use_r2

# Chaves no bucket (prefixo branding/) — não versionar binários no static/.
HOME_HERO_KEY = "branding/home-hero.jpg"
HOME_CAT_HVAC_KEY = "branding/home-cat-hvac.jpg"
HOME_CAT_KITCHEN_KEY = "branding/home-cat-kitchen.jpg"


def branding_image_url(storage_key: str) -> str:
    """URL assinada no R2; vazio se storage local/teste sem objeto."""
    if not storage_key:
        return ""
    if use_r2():
        return signed_url(storage_key) or ""
    # Testes / filesystem: tenta default_storage.url
    from django.core.files.storage import default_storage

    try:
        if default_storage.exists(storage_key):
            return default_storage.url(storage_key)
    except Exception:  # noqa: BLE001
        return ""
    return ""


def home_branding_urls() -> dict[str, str]:
    return {
        "home_hero_url": branding_image_url(HOME_HERO_KEY),
        "home_cat_hvac_url": branding_image_url(HOME_CAT_HVAC_KEY),
        "home_cat_kitchen_url": branding_image_url(HOME_CAT_KITCHEN_KEY),
    }
