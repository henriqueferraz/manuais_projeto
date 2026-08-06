"""Chunking semântico de manuais (seção/parágrafo; preserva tabelas)."""

from __future__ import annotations

import re
from dataclasses import dataclass

from django.conf import settings


@dataclass(frozen=True)
class TextChunk:
    content: str
    section: str
    page: int | None
    chunk_index: int
    metadata: dict


_SECTION_RE = re.compile(
    r"(?m)^(#{1,3}\s+.+$|[A-ZÁÉÍÓÚÂÊÔÃÕÇ][A-ZÁÉÍÓÚÂÊÔÃÕÇ0-9\s\-–—/]{4,80}$|"
    r"\d+(?:\.\d+)*\s+[A-ZÁÉÍÓÚ][^\n]{3,80}$)"
)
_PAGE_RE = re.compile(r"(?i)(?:página|page|pág\.?)\s*[:\-]?\s*(\d+)")
_TABLE_LINE_RE = re.compile(r".*\|.*\|.*")


def chunk_manual_text(text: str) -> list[TextChunk]:
    """Divide texto limpo em chunks por seção/parágrafo semântico."""
    cleaned = (text or "").strip()
    if not cleaned:
        return []

    max_chars = int(getattr(settings, "RAG_CHUNK_SIZE", 900))
    overlap = int(getattr(settings, "RAG_CHUNK_OVERLAP", 120))
    sections = _split_sections(cleaned)
    chunks: list[TextChunk] = []
    idx = 0

    for section_title, body, page in sections:
        parts = _split_preserving_tables(body, max_chars=max_chars, overlap=overlap)
        for part in parts:
            content = part.strip()
            if len(content) < 40:
                continue
            chunks.append(
                TextChunk(
                    content=content,
                    section=section_title[:255],
                    page=page,
                    chunk_index=idx,
                    metadata={
                        "has_table": bool(_TABLE_LINE_RE.search(content)),
                        "char_len": len(content),
                    },
                )
            )
            idx += 1
    return chunks


def _split_sections(text: str) -> list[tuple[str, str, int | None]]:
    matches = list(_SECTION_RE.finditer(text))
    if not matches:
        page = _detect_page(text)
        return [("Geral", text, page)]

    sections: list[tuple[str, str, int | None]] = []
    if matches[0].start() > 0:
        preamble = text[: matches[0].start()].strip()
        if preamble:
            sections.append(("Introdução", preamble, _detect_page(preamble)))

    for i, match in enumerate(matches):
        start = match.start()
        end = matches[i + 1].start() if i + 1 < len(matches) else len(text)
        title = match.group(0).strip().lstrip("#").strip()
        body = text[match.end() : end].strip()
        page = _detect_page(text[start:end]) or _detect_page(title)
        sections.append((title or f"Seção {i + 1}", body or title, page))
    return sections


def _split_preserving_tables(text: str, *, max_chars: int, overlap: int) -> list[str]:
    blocks = _paragraph_blocks(text)
    parts: list[str] = []
    buf = ""
    for block in blocks:
        candidate = f"{buf}\n\n{block}".strip() if buf else block
        if len(candidate) <= max_chars:
            buf = candidate
            continue
        if buf:
            parts.append(buf)
            tail = buf[-overlap:] if overlap and len(buf) > overlap else ""
            buf = f"{tail}\n\n{block}".strip() if tail else block
        else:
            # bloco único longo (tabela larga): corta por linhas
            parts.extend(_hard_split(block, max_chars=max_chars, overlap=overlap))
            buf = ""
    if buf:
        parts.append(buf)
    return parts


def _paragraph_blocks(text: str) -> list[str]:
    lines = text.splitlines()
    blocks: list[str] = []
    current: list[str] = []
    in_table = False

    def flush() -> None:
        nonlocal current
        if current:
            blocks.append("\n".join(current).strip())
            current = []

    for line in lines:
        is_table = bool(_TABLE_LINE_RE.match(line))
        if is_table:
            if not in_table and current:
                flush()
            in_table = True
            current.append(line)
            continue
        if in_table:
            flush()
            in_table = False
        if not line.strip():
            flush()
            continue
        current.append(line)
    flush()
    return [b for b in blocks if b]


def _hard_split(text: str, *, max_chars: int, overlap: int) -> list[str]:
    if len(text) <= max_chars:
        return [text]
    parts: list[str] = []
    start = 0
    while start < len(text):
        end = min(len(text), start + max_chars)
        parts.append(text[start:end])
        if end >= len(text):
            break
        start = max(end - overlap, start + 1)
    return parts


def _detect_page(text: str) -> int | None:
    match = _PAGE_RE.search(text or "")
    if not match:
        return None
    try:
        return int(match.group(1))
    except ValueError:
        return None
