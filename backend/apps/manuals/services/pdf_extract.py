"""Extração de texto/tabelas de PDF (pdfplumber; OCR stub se escaneado)."""

from __future__ import annotations

import io
from dataclasses import dataclass, field

import pdfplumber
import structlog

logger = structlog.get_logger(__name__)

MIN_NATIVE_CHARS = 80


@dataclass
class PdfExtraction:
    text: str
    page_count: int
    used_ocr: bool = False
    tables: list[list[list[str | None]]] = field(default_factory=list)


def extract_pdf_text(content: bytes, *, max_pages: int = 40) -> PdfExtraction:
    """
    Extrai texto e tabelas. Se o PDF parecer escaneado (pouco texto),
    marca used_ocr=True e tenta OCR se MANUAL_OCR_ENABLED (stub/opcional).
    """
    tables: list[list[list[str | None]]] = []
    pages_text: list[str] = []

    with pdfplumber.open(io.BytesIO(content)) as pdf:
        page_count = len(pdf.pages)
        for i, page in enumerate(pdf.pages[:max_pages]):
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
        ocr_text = _try_ocr(content)
        if ocr_text:
            text = ocr_text
            used_ocr = True
        else:
            used_ocr = True  # sinaliza que seria necessário OCR
            logger.info("pdf_looks_scanned", chars=len(text), pages=page_count)

    # Anexa resumo tabular simples ao texto para o LLM
    if tables:
        table_blobs = []
        for idx, table in enumerate(tables[:15]):
            rows = [" | ".join((c or "").strip() for c in row) for row in table if row]
            table_blobs.append(f"[Tabela {idx + 1}]\n" + "\n".join(rows))
        text = text + "\n\n" + "\n\n".join(table_blobs)

    return PdfExtraction(text=text, page_count=page_count, used_ocr=used_ocr, tables=tables)


def _try_ocr(content: bytes) -> str:
    """OCR opcional — só se MANUAL_OCR_ENABLED e dependências presentes."""
    from django.conf import settings

    if not getattr(settings, "MANUAL_OCR_ENABLED", False):
        return ""
    try:
        from pypdf import PdfReader  # noqa: F401 — presença mínima

        # Stub: integração real com pytesseract/unstructured fica como upgrade
        logger.warning("ocr_enabled_but_not_implemented", size=len(content))
    except Exception as exc:  # noqa: BLE001
        logger.warning("ocr_unavailable", error=str(exc))
    return ""
