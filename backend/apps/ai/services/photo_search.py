"""Busca de peça por foto (Claude vision / mock) — F6 / T-6.3."""

from __future__ import annotations

import base64
import time
import uuid
from pathlib import Path

import structlog
from django.conf import settings
from django.core.exceptions import ValidationError
from django.core.files.base import ContentFile
from django.db.models import Q
from django.utils import timezone

from apps.ai.models import PhotoSearch
from apps.products.models import Product

logger = structlog.get_logger(__name__)

ALLOWED_PHOTO_MIMES = {"image/jpeg", "image/png", "image/webp"}
_JPEG = b"\xff\xd8\xff"
_PNG = b"\x89PNG\r\n\x1a\n"
_WEBP_RIFF = b"RIFF"


def photo_max_bytes() -> int:
    return int(getattr(settings, "PHOTO_MAX_UPLOAD_BYTES", 5 * 1024 * 1024))


def sniff_image_mime(content: bytes, filename: str = "") -> str:
    if content.startswith(_JPEG):
        return "image/jpeg"
    if content.startswith(_PNG):
        return "image/png"
    if content[:4] == _WEBP_RIFF and b"WEBP" in content[8:16]:
        return "image/webp"
    lower = filename.lower()
    if lower.endswith((".jpg", ".jpeg")):
        return "image/jpeg"
    if lower.endswith(".png"):
        return "image/png"
    if lower.endswith(".webp"):
        return "image/webp"
    return "application/octet-stream"


def validate_photo_upload(content: bytes, filename: str) -> tuple[bytes, str]:
    if not content:
        raise ValidationError("Arquivo vazio.")
    if len(content) > photo_max_bytes():
        raise ValidationError(f"Imagem excede o limite de {photo_max_bytes() // (1024 * 1024)} MB.")
    mime = sniff_image_mime(content, filename)
    if mime not in ALLOWED_PHOTO_MIMES:
        raise ValidationError("Formato inválido. Use JPEG, PNG ou WebP.")
    return content, mime


def create_photo_search(
    *,
    content: bytes,
    filename: str,
    user=None,
    anonymous_key: str = "",
    product_id: int | None = None,
    enqueue: bool = True,
) -> PhotoSearch:
    validated, mime = validate_photo_upload(content, filename)
    search = PhotoSearch(
        user=user if getattr(user, "is_authenticated", False) else None,
        anonymous_key=anonymous_key if not getattr(user, "is_authenticated", False) else "",
        product_id=product_id,
        original_filename=Path(filename).name[:255],
        mime_type=mime,
        size_bytes=len(validated),
        status=PhotoSearch.Status.PENDING,
    )
    safe_name = Path(filename).name.replace(" ", "_")[:120]
    search.image.save(safe_name, ContentFile(validated), save=False)
    search.save()

    if enqueue:
        from apps.ai.tasks import photo_search_task

        photo_search_task.delay(str(search.pk))
    return search


def run_photo_search(search_id: str | uuid.UUID) -> PhotoSearch:
    search = PhotoSearch.objects.get(pk=search_id)
    search.status = PhotoSearch.Status.RUNNING
    search.started_at = timezone.now()
    search.save(update_fields=["status", "started_at", "updated_at"])
    started = time.perf_counter()

    try:
        content = search.image.read()
        if hasattr(search.image, "seek"):
            search.image.seek(0)
        mode = getattr(settings, "PHOTO_LLM_MODE", "mock").lower()
        if mode == "anthropic":
            candidates = _vision_anthropic(content, search.mime_type)
        else:
            candidates = _vision_mock(content, search)
        search.candidates = candidates
        search.status = PhotoSearch.Status.DONE
        search.error_message = ""
        search.model_name = "anthropic-vision" if mode == "anthropic" else "mock-vision"
    except Exception as exc:  # noqa: BLE001
        logger.exception("photo_search_failed", search_id=str(search.pk))
        search.status = PhotoSearch.Status.FAILED
        search.error_message = str(exc)[:2000]
        search.candidates = []
    finally:
        search.latency_ms = int((time.perf_counter() - started) * 1000)
        search.finished_at = timezone.now()
        search.save()
    return search


def _vision_mock(content: bytes, search: PhotoSearch) -> list[dict]:
    """
    Mock determinístico: ranqueia peças publicadas por keywords do filename
    e/ou produto vinculado; se nada, top spares.
    """
    name = (search.original_filename or "").lower()
    q = Q(status=Product.Status.PUBLISHED, product_kind=Product.Kind.SPARE_PART)
    scored: list[tuple[float, Product]] = []
    qs = Product.objects.filter(q).select_related("stock").prefetch_related("translations")[:40]
    for product in qs:
        score = 0.35
        blob = f"{product.sku} {product.model_code} {product.brand}".lower()
        for tr in product.translations.all():
            blob += f" {tr.name}".lower()
        if "cap" in name and "cap" in blob:
            score += 0.4
        if "pa" in name or "blade" in name:
            if "pa" in blob or "pá" in blob:
                score += 0.35
        if search.product_id and product.pk != search.product_id:
            score += 0.05
        scored.append((score, product))
    scored.sort(key=lambda x: x[0], reverse=True)
    if not scored:
        return []
    out = []
    for score, product in scored[:5]:
        label = product.sku
        tr = product.translations.first()
        if tr:
            label = f"{product.sku} — {tr.name}"
        out.append(
            {
                "sku": product.sku,
                "product_id": product.pk,
                "label": label,
                "score": round(min(0.98, score), 3),
                "reason": "Correspondência heurística (mock vision)",
            }
        )
    return out


def _vision_anthropic(content: bytes, mime: str) -> list[dict]:
    from langchain_anthropic import ChatAnthropic
    from langchain_core.messages import HumanMessage

    b64 = base64.standard_b64encode(content).decode("ascii")
    media = mime or "image/jpeg"
    llm = ChatAnthropic(
        model=getattr(settings, "ANTHROPIC_MODEL", "claude-sonnet-4-5-20250929"),
        api_key=settings.ANTHROPIC_API_KEY or None,
        temperature=0,
        max_tokens=800,
    )
    catalog = list(
        Product.objects.filter(
            status=Product.Status.PUBLISHED,
            product_kind=Product.Kind.SPARE_PART,
        ).values_list("sku", "brand", "model_code")[:80]
    )
    catalog_txt = "\n".join(f"- {sku} | {brand} | {model}" for sku, brand, model in catalog)
    msg = HumanMessage(
        content=[
            {
                "type": "text",
                "text": (
                    "Identifique a peça na foto e rode candidatos do catálogo abaixo. "
                    "Responda JSON: "
                    '[{"sku":"...","score":0.0,"reason":"..."}]. '
                    f"Catálogo:\n{catalog_txt or '(vazio)'}"
                ),
            },
            {
                "type": "image",
                "source": {"type": "base64", "media_type": media, "data": b64},
            },
        ]
    )
    result = llm.invoke([msg])
    text = str(result.content)
    # Parsing mínimo — se falhar, retorna vazio
    import json
    import re

    match = re.search(r"\[.*\]", text, re.S)
    if not match:
        return []
    try:
        raw = json.loads(match.group(0))
    except json.JSONDecodeError:
        return []
    out = []
    for row in raw[:5]:
        sku = str(row.get("sku") or "")
        if not sku:
            continue
        product = Product.objects.filter(sku=sku, status=Product.Status.PUBLISHED).first()
        out.append(
            {
                "sku": sku,
                "product_id": product.pk if product else None,
                "label": sku,
                "score": float(row.get("score") or 0.5),
                "reason": str(row.get("reason") or "")[:240],
            }
        )
    return out
