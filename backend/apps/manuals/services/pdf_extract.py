"""Extração de texto/tabelas de PDF (pdfplumber; OCR com pypdfium2 + Tesseract)."""

from __future__ import annotations

import io
from dataclasses import dataclass, field

import pdfplumber
import structlog
from django.conf import settings

logger = structlog.get_logger(__name__)

MIN_NATIVE_CHARS = 80
# PSM 6 = bloco uniforme de texto (manuais/fichas); ajuda scans medianos
_OCR_TESSERACT_CONFIG = "--oem 3 --psm 6"


@dataclass
class PdfExtraction:
    text: str
    page_count: int
    used_ocr: bool = False
    tables: list[list[list[str | None]]] = field(default_factory=list)


def extract_pdf_text(content: bytes, *, max_pages: int | None = None) -> PdfExtraction:
    """
    Extrai texto e tabelas. Se o PDF parecer escaneado (pouco texto),
    tenta OCR quando MANUAL_OCR_ENABLED=true (pypdfium2 + Tesseract).
    """
    pages_limit = max_pages
    if pages_limit is None:
        pages_limit = int(getattr(settings, "MANUAL_OCR_MAX_PAGES", 40) or 40)

    tables: list[list[list[str | None]]] = []
    pages_text: list[str] = []

    with pdfplumber.open(io.BytesIO(content)) as pdf:
        page_count = len(pdf.pages)
        for i, page in enumerate(pdf.pages[:pages_limit]):
            page_text = page.extract_text() or ""
            pages_text.append(page_text)
            try:
                for table in page.extract_tables() or []:
                    tables.append(table)
            except Exception as exc:  # noqa: BLE001
                logger.warning("pdf_table_extract_failed", page=i, error=str(exc))

    text = "\n\n".join(p for p in pages_text if p).strip()
    used_ocr = False

    if len(text) < MIN_NATIVE_CHARS:
        logger.info("pdf_looks_scanned", chars=len(text), pages=page_count)
        ocr_text = _try_ocr(content, max_pages=pages_limit)
        if ocr_text.strip():
            text = ocr_text.strip()
            used_ocr = True
        else:
            used_ocr = True

    # Anexa resumo tabular simples ao texto para o LLM
    if tables:
        table_blobs = []
        for idx, table in enumerate(tables[:15]):
            rows = [" | ".join((c or "").strip() for c in row) for row in table if row]
            table_blobs.append(f"[Tabela {idx + 1}]\n" + "\n".join(rows))
        text = text + "\n\n" + "\n\n".join(table_blobs)

    return PdfExtraction(text=text, page_count=page_count, used_ocr=used_ocr, tables=tables)


def preprocess_ocr_image(image):
    """
    Melhora scans medianos antes do Tesseract: cinza, contraste, nitidez e deskew leve.

    Aceita PIL.Image; devolve PIL.Image em modo L (escala de cinza).
    """
    from PIL import Image, ImageEnhance, ImageFilter, ImageOps

    img = image
    if img.mode not in {"L", "RGB", "RGBA"}:
        img = img.convert("RGB")
    if img.mode == "RGBA":
        background = Image.new("RGB", img.size, (255, 255, 255))
        background.paste(img, mask=img.split()[-1])
        img = background
    if img.mode != "L":
        img = img.convert("L")

    img = ImageOps.autocontrast(img, cutoff=1)
    img = ImageEnhance.Contrast(img).enhance(1.35)
    img = ImageEnhance.Sharpness(img).enhance(1.4)
    img = img.filter(ImageFilter.MedianFilter(size=3))

    angle = _estimate_skew_angle(img)
    if abs(angle) >= 0.4:
        img = img.rotate(angle, expand=True, fillcolor=255, resample=Image.Resampling.BICUBIC)
        img = ImageOps.autocontrast(img, cutoff=1)

    # Upscale leve se a página renderizada ficou pequena (ajuda Tesseract)
    width, height = img.size
    min_side = min(width, height)
    if min_side < 1200:
        factor = 1200 / float(min_side)
        new_size = (max(1, int(width * factor)), max(1, int(height * factor)))
        img = img.resize(new_size, Image.Resampling.LANCZOS)

    return img


def _estimate_skew_angle(img, *, max_angle: float = 5.0, step: float = 0.5) -> float:
    """Estima ângulo de inclinação (±max_angle) pela projeção horizontal."""
    from PIL import Image

    # Amostra reduzida para custo baixo
    sample = img
    max_w = 900
    if sample.width > max_w:
        ratio = max_w / float(sample.width)
        sample = sample.resize(
            (max_w, max(1, int(sample.height * ratio))),
            Image.Resampling.BILINEAR,
        )

    best_angle = 0.0
    best_score = -1.0
    angle = -max_angle
    while angle <= max_angle + 1e-9:
        rotated = sample.rotate(angle, expand=False, fillcolor=255)
        # Binário simples: tinta escura = 1
        pixels = rotated.point(lambda p: 1 if p < 180 else 0)
        # Soma por linha; linhas de texto geram picos → maior variância
        hist = []
        px = pixels.load()
        w, h = pixels.size
        for y in range(h):
            row_sum = 0
            for x in range(w):
                row_sum += px[x, y]
            hist.append(row_sum)
        if len(hist) < 2:
            angle += step
            continue
        mean = sum(hist) / len(hist)
        var = sum((v - mean) ** 2 for v in hist) / len(hist)
        if var > best_score:
            best_score = var
            best_angle = angle
        angle += step
    return best_angle


def _try_ocr(content: bytes, *, max_pages: int = 40) -> str:
    """
    OCR de PDF escaneado: renderiza páginas (pypdfium2), pré-processa e lê com Tesseract.

    Requer MANUAL_OCR_ENABLED=true, pacote pytesseract e binário tesseract-ocr
    (com idioma pt, se disponível).
    """
    if not getattr(settings, "MANUAL_OCR_ENABLED", False):
        logger.info("ocr_skipped_disabled")
        return ""

    try:
        import pypdfium2 as pdfium
        import pytesseract
    except ImportError as exc:
        logger.warning("ocr_dependencies_missing", error=str(exc))
        return ""

    langs = (getattr(settings, "MANUAL_OCR_LANGS", "por+eng") or "por+eng").strip()
    scale = float(getattr(settings, "MANUAL_OCR_SCALE", 2.5) or 2.5)
    page_limit = max(1, int(max_pages or 40))

    try:
        doc = pdfium.PdfDocument(content)
    except Exception as exc:  # noqa: BLE001
        logger.warning("ocr_pdf_open_failed", error=str(exc))
        return ""

    chunks: list[str] = []
    try:
        total = len(doc)
        for index in range(min(total, page_limit)):
            page = doc[index]
            try:
                bitmap = page.render(scale=scale)
                pil = bitmap.to_pil()
                prepared = preprocess_ocr_image(pil)
                text = (
                    pytesseract.image_to_string(
                        prepared,
                        lang=langs,
                        config=_OCR_TESSERACT_CONFIG,
                    )
                    or ""
                )
                text = text.strip()
                if text:
                    chunks.append(text)
            except pytesseract.TesseractNotFoundError:
                logger.warning("ocr_tesseract_binary_missing")
                return ""
            except Exception as exc:  # noqa: BLE001
                logger.warning("ocr_page_failed", page=index, error=str(exc))
            finally:
                page.close()
    finally:
        doc.close()

    joined = "\n\n".join(chunks).strip()
    logger.info(
        "ocr_completed",
        pages=len(chunks),
        chars=len(joined),
        langs=langs,
        scale=scale,
    )
    return joined
