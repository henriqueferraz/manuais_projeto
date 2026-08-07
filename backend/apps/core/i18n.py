"""Resolução de locale (F8 / ADR-0001)."""

from __future__ import annotations

from django.http import HttpRequest

SUPPORTED = ("pt-BR", "en", "es")
DEFAULT_LOCALE = "pt-BR"
COOKIE = "tp_lang"

_LANG_MAP = {
    "pt": "pt-BR",
    "pt-br": "pt-BR",
    "en": "en",
    "en-us": "en",
    "es": "es",
    "es-es": "es",
    "es-mx": "es",
}


def normalize_locale(raw: str | None) -> str:
    if not raw:
        return DEFAULT_LOCALE
    key = raw.strip().replace("_", "-")
    if key in SUPPORTED:
        return key
    return _LANG_MAP.get(key.lower(), DEFAULT_LOCALE)


def resolve_locale(request: HttpRequest | None = None, *, explicit: str | None = None) -> str:
    if explicit:
        return normalize_locale(explicit)
    if request is None:
        return DEFAULT_LOCALE
    q = request.GET.get("lang") or request.POST.get("lang")
    if q:
        return normalize_locale(q)
    cookie = request.COOKIES.get(COOKIE)
    if cookie:
        return normalize_locale(cookie)
    accept = request.META.get("HTTP_ACCEPT_LANGUAGE", "")
    if accept:
        primary = accept.split(",")[0].split(";")[0].strip()
        return normalize_locale(primary)
    return DEFAULT_LOCALE


def detect_text_locale(text: str) -> str:
    """Heurística leve para idioma do relato (chat)."""
    t = (text or "").lower()
    en_hits = sum(
        1 for w in (" the ", " what ", " how ", " does ", " not ", " fan ") if w in f" {t} "
    )
    es_hits = sum(
        1 for w in (" el ", " la ", " qué ", " como ", " no ", " ventilador ") if w in f" {t} "
    )
    if en_hits >= 2 and en_hits > es_hits:
        return "en"
    if es_hits >= 2 and es_hits > en_hits:
        return "es"
    return "pt-BR"
