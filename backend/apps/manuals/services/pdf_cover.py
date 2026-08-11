"""Gera capa (1ª página) de um PDF para usar como foto de produto."""

from __future__ import annotations

import logging
from io import BytesIO

from django.core.files.uploadedfile import InMemoryUploadedFile

logger = logging.getLogger(__name__)


def render_pdf_first_page_jpeg(content: bytes, *, scale: float = 2.0) -> bytes | None:
    """
    Renderiza a primeira página do PDF em JPEG.

    Retorna None se o PDF for inválido ou não tiver páginas.
    """
    if not content:
        return None
    try:
        import pypdfium2 as pdfium
    except ImportError:
        logger.warning("pypdfium2_unavailable")
        return None

    try:
        doc = pdfium.PdfDocument(content)
    except Exception:  # noqa: BLE001
        logger.exception("pdf_cover_open_failed")
        return None

    try:
        if len(doc) < 1:
            return None
        page = doc[0]
        bitmap = page.render(scale=scale)
        pil = bitmap.to_pil()
        buf = BytesIO()
        pil.convert("RGB").save(buf, format="JPEG", quality=85, optimize=True)
        return buf.getvalue()
    except Exception:  # noqa: BLE001
        logger.exception("pdf_cover_render_failed")
        return None
    finally:
        try:
            doc.close()
        except Exception:  # noqa: BLE001  # nosec B110
            pass


def pdf_cover_as_upload(
    content: bytes,
    *,
    filename: str = "manual-capa.jpg",
) -> InMemoryUploadedFile | None:
    """Empacota a capa do PDF como upload pronto para prepare_product_image."""
    jpeg = render_pdf_first_page_jpeg(content)
    if not jpeg:
        return None
    buf = BytesIO(jpeg)
    buf.seek(0)
    name = filename if filename.lower().endswith((".jpg", ".jpeg")) else "manual-capa.jpg"
    return InMemoryUploadedFile(
        file=buf,
        field_name="images",
        name=name,
        content_type="image/jpeg",
        size=len(jpeg),
        charset=None,
    )
