"""Busca de fotos de produto na internet (ddgs) + download seguro para o cadastro."""

from __future__ import annotations

import ipaddress
import socket
from io import BytesIO
from pathlib import Path
from typing import Any
from urllib.error import HTTPError, URLError
from urllib.parse import urlparse
from urllib.request import Request, urlopen

import structlog
from django.conf import settings
from django.core.exceptions import ValidationError
from django.core.files.uploadedfile import InMemoryUploadedFile
from PIL import Image

logger = structlog.get_logger(__name__)

WEB_IMAGE_MAX_RESULTS = 5
WEB_IMAGE_DOWNLOAD_MAX_BYTES = 10 * 1024 * 1024
WEB_IMAGE_DOWNLOAD_TIMEOUT = 12
_ALLOWED_SCHEMES = {"http", "https"}
_BLOCKED_HOST_SUFFIXES = (".localhost", ".local", ".internal")


def web_image_search_mode() -> str:
    """Retorna o modo de busca de fotos web (`mock` ou provedor configurado)."""
    return str(getattr(settings, "WEB_IMAGE_SEARCH_MODE", "mock") or "mock").lower()


def build_image_search_query(
    *,
    brand: str = "",
    model: str = "",
    appliance_type: str = "",
    name: str = "",
) -> str:
    """Monta a query a partir de marca, modelo e tipo de aparelho."""
    parts = [
        (brand or "").strip(),
        (model or "").strip(),
        (appliance_type or "").strip(),
        (name or "").strip(),
    ]
    # Evita repetir o nome se já estiver embutido em marca/modelo.
    seen: list[str] = []
    for part in parts:
        if not part:
            continue
        low = part.casefold()
        if any(low in s.casefold() or s.casefold() in low for s in seen):
            continue
        seen.append(part)
    query = " ".join(seen).strip()
    if not query:
        raise ValidationError("Informe marca, modelo ou tipo de aparelho para buscar fotos.")
    return f"{query} produto foto"


def search_product_web_images(
    *,
    brand: str = "",
    model: str = "",
    appliance_type: str = "",
    name: str = "",
    max_results: int = WEB_IMAGE_MAX_RESULTS,
) -> dict[str, Any]:
    """
    Busca até ``max_results`` fotos na internet.
    Modo ``mock`` (CI/local sem rede) devolve candidatos determinísticos.
    """
    query = build_image_search_query(
        brand=brand,
        model=model,
        appliance_type=appliance_type,
        name=name,
    )
    limit = max(1, min(int(max_results or WEB_IMAGE_MAX_RESULTS), WEB_IMAGE_MAX_RESULTS))
    mode = web_image_search_mode()

    if mode == "ddgs":
        candidates = _search_ddgs(query, limit=limit)
    else:
        candidates = _search_mock(query, limit=limit)

    return {
        "ok": True,
        "query": query,
        "mode": mode,
        "candidates": candidates,
        "message": (
            f"{len(candidates)} opção(ões) encontrada(s). "
            "Marque uma ou mais para inserir ao salvar, ou nenhuma."
            if candidates
            else "Nenhuma foto encontrada para esses dados."
        ),
    }


def fetch_web_image_as_upload(
    url: str,
    *,
    filename: str = "web-product.jpg",
) -> InMemoryUploadedFile:
    """Baixa a imagem escolhida (com anti-SSRF) ou gera JPEG sintético no modo mock."""
    cleaned = (url or "").strip()
    if not cleaned:
        raise ValidationError("Nenhuma URL de imagem selecionada.")

    mode = web_image_search_mode()
    if mode != "ddgs" or cleaned.startswith("https://example.invalid/"):
        return _synthetic_upload(filename=filename)

    _assert_safe_image_url(cleaned)
    try:
        req = Request(
            cleaned,
            headers={
                "User-Agent": "TechPartsAI/1.0 (+product-cadastro; image-preview)",
                "Accept": "image/jpeg,image/png,image/webp,*/*",
            },
            method="GET",
        )
        with urlopen(req, timeout=WEB_IMAGE_DOWNLOAD_TIMEOUT) as resp:  # nosec B310
            content_type = (resp.headers.get("Content-Type") or "").split(";")[0].strip().lower()
            raw = resp.read(WEB_IMAGE_DOWNLOAD_MAX_BYTES + 1)
    except HTTPError as exc:
        raise ValidationError(f"Falha ao baixar a imagem (HTTP {exc.code}).") from exc
    except URLError as exc:
        raise ValidationError("Não foi possível baixar a imagem selecionada.") from exc
    except TimeoutError as exc:
        raise ValidationError("Tempo esgotado ao baixar a imagem.") from exc

    if len(raw) > WEB_IMAGE_DOWNLOAD_MAX_BYTES:
        raise ValidationError("Imagem remota muito grande (máx. 10 MB).")
    if len(raw) < 64:
        raise ValidationError("Arquivo remoto inválido ou vazio.")

    ext, mime = _sniff_image(raw, content_type=content_type, url=cleaned)
    safe_name = Path(filename).stem or "web-product"
    safe_name = "".join(ch if ch.isalnum() or ch in "-_" else "-" for ch in safe_name).strip("-")
    out_name = f"{safe_name or 'web-product'}{ext}"
    buf = BytesIO(raw)
    return InMemoryUploadedFile(
        file=buf,
        field_name="images",
        name=out_name,
        content_type=mime,
        size=len(raw),
        charset=None,
    )


def _search_ddgs(query: str, *, limit: int) -> list[dict[str, Any]]:
    try:
        from ddgs import DDGS
    except ImportError as exc:  # pragma: no cover - ambiente sem dep
        raise ValidationError(
            "Pacote ddgs não instalado. Use WEB_IMAGE_SEARCH_MODE=mock ou instale ddgs."
        ) from exc

    rows: list[dict[str, Any]] = []
    try:
        with DDGS() as client:
            raw_items = list(client.images(query, max_results=limit))
    except Exception as exc:  # noqa: BLE001
        logger.exception("web_image_search_ddgs_failed", query=query)
        raise ValidationError(f"Falha na busca de imagens: {exc}") from exc

    for idx, item in enumerate(raw_items[:limit]):
        image_url = str(item.get("image") or "").strip()
        if not image_url:
            continue
        rows.append(
            {
                "id": str(idx + 1),
                "title": str(item.get("title") or "Foto encontrada")[:180],
                "image_url": image_url,
                "thumbnail_url": str(item.get("thumbnail") or image_url),
                "source_url": str(item.get("url") or item.get("source") or "")[:500],
            }
        )
    return rows


def _search_mock(query: str, *, limit: int) -> list[dict[str, Any]]:
    """Candidatos determinísticos (sem rede) para CI e demos locais."""
    slug = "-".join(query.casefold().split())[:48] or "produto"
    rows: list[dict[str, Any]] = []
    for i in range(1, limit + 1):
        image_url = f"https://example.invalid/web-product/{slug}-{i}.jpg"
        rows.append(
            {
                "id": str(i),
                "title": f"Sugestão {i} · {query}"[:180],
                "image_url": image_url,
                "thumbnail_url": image_url,
                "source_url": f"https://example.invalid/fonte/{slug}-{i}",
            }
        )
    return rows


def _synthetic_upload(*, filename: str) -> InMemoryUploadedFile:
    """JPEG 800×800 sintético para modo mock / URLs de teste."""
    img = Image.new("RGB", (800, 800), color=(32, 96, 160))
    buf = BytesIO()
    img.save(buf, format="JPEG", quality=85, optimize=True)
    buf.seek(0)
    safe = Path(filename).stem or "web-product"
    out_name = f"{safe}.jpg"
    return InMemoryUploadedFile(
        file=buf,
        field_name="images",
        name=out_name,
        content_type="image/jpeg",
        size=buf.getbuffer().nbytes,
        charset=None,
    )


def _assert_safe_image_url(url: str) -> None:
    parsed = urlparse(url)
    if parsed.scheme.lower() not in _ALLOWED_SCHEMES:
        raise ValidationError("URL de imagem inválida (use http/https).")
    host = (parsed.hostname or "").strip().lower()
    if not host:
        raise ValidationError("URL de imagem sem host.")
    if host == "localhost" or any(host.endswith(suf) for suf in _BLOCKED_HOST_SUFFIXES):
        raise ValidationError("Host de imagem não permitido.")
    if host in {"metadata.google.internal", "metadata"}:
        raise ValidationError("Host de imagem não permitido.")

    try:
        infos = socket.getaddrinfo(host, None)
    except socket.gaierror as exc:
        raise ValidationError("Não foi possível resolver o host da imagem.") from exc

    for info in infos:
        ip_str = info[4][0]
        try:
            ip = ipaddress.ip_address(ip_str)
        except ValueError:
            continue
        if (
            ip.is_private
            or ip.is_loopback
            or ip.is_link_local
            or ip.is_reserved
            or ip.is_multicast
            or ip.is_unspecified
        ):
            raise ValidationError("Host de imagem aponta para rede privada.")


def _sniff_image(raw: bytes, *, content_type: str, url: str) -> tuple[str, str]:
    if raw.startswith(b"\xff\xd8\xff"):
        return ".jpg", "image/jpeg"
    if raw.startswith(b"\x89PNG\r\n\x1a\n"):
        return ".png", "image/png"
    if raw[:4] == b"RIFF" and b"WEBP" in raw[8:16]:
        return ".webp", "image/webp"

    if content_type in {"image/jpeg", "image/jpg"}:
        return ".jpg", "image/jpeg"
    if content_type == "image/png":
        return ".png", "image/png"
    if content_type == "image/webp":
        return ".webp", "image/webp"

    ext = Path(urlparse(url).path).suffix.lower()
    if ext in {".jpg", ".jpeg"}:
        return ".jpg", "image/jpeg"
    if ext == ".png":
        return ".png", "image/png"
    if ext == ".webp":
        return ".webp", "image/webp"

    raise ValidationError("A URL não aponta para uma imagem JPG/PNG/WEBP.")
