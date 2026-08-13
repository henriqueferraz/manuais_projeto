"""Chunking semântico de manuais (seção/parágrafo; preserva tabelas)."""

from __future__ import annotations

import re
from dataclasses import dataclass

from django.conf import settings


@dataclass(frozen=True)
class TextChunk:
    """Fragmento de manual pronto para embed (conteúdo, seção, página)."""

    content: str
    section: str
    page: int | None
    chunk_index: int
    metadata: dict


# Títulos: markdown, ALL CAPS (com indentação) ou numeração 1.2 Estilo.
# Importante: NÃO usar \s genérico (pega \n) — senão "8\\n\\nSUCO…" vira um título só.
_SECTION_CANDIDATE_RE = re.compile(
    r"(?m)^[ \t]*(?:#{1,3}[ \t]+[^\n]+|"
    r"[A-ZÁÉÍÓÚÂÊÔÃÕÇ][A-ZÁÉÍÓÚÂÊÔÃÕÇ0-9 \t\-–—/'“”\"]{4,80}|"
    r"\d+(?:\.\d+)*[ \t]+[A-ZÁÉÍÓÚ][^\n]{3,80})$"
)
# Linhas de ingredientes / medidas NÃO são seções (causava "1 Laranja; Açúcar…").
_INGREDIENTISH_RE = re.compile(
    r"(?i)("
    r"^\d|"
    r";|"
    r"\b(xícaras?|colheres?|ovos?|latas?|envelope|gotinhas|cubos?|"
    r"mamões|cenouras?|mangas?|ml\b|gramas?|\bg\b|\bkg\b)\b|"
    r"^\s*ingredientes?\s*$|"
    r"^\s*modo de preparo\s*$"
    r")"
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
        # Garante que o título da receita entre no texto indexado.
        full_body = body.strip()
        if section_title and section_title not in ("Geral", "Introdução"):
            if section_title.lower() not in full_body.lower():
                full_body = f"{section_title}\n{full_body}".strip()
        parts = _split_preserving_tables(full_body, max_chars=max_chars, overlap=overlap)
        for part in parts:
            content = part.strip()
            # Receitas curtas (título + poucos ingredientes) ainda devem indexar.
            min_len = 24 if section_title not in ("Geral", "Introdução") else 40
            if len(content) < min_len:
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


def _is_section_title(line: str) -> bool:
    raw = (line or "").strip()
    if not raw or not _SECTION_CANDIDATE_RE.match(raw):
        return False
    # Subtítulos de receita NÃO quebram a seção (senão "SUCO DE CENOURA" fica sem corpo).
    if re.match(r"(?i)^(ingredientes?|modo de preparo|preparo|rendimento)$", raw):
        return False
    if _INGREDIENTISH_RE.search(raw) and not re.match(
        r"(?i)^(suco|mousse|massa|milk|vitamina|receita|usando|instruções|creme|pudim)\b",
        raw,
    ):
        # Ex.: "2 Cenouras…", "1 Laranja; Açúcar a gosto"
        if re.search(r"\d", raw) or ";" in raw:
            return False
    # ALL CAPS curto com só unidades → rejeita
    letters = re.sub(r"[^A-Za-zÁ-ú]", "", raw)
    if len(letters) < 6:
        return False
    return True


def _split_sections(text: str) -> list[tuple[str, str, int | None]]:
    matches = [m for m in _SECTION_CANDIDATE_RE.finditer(text) if _is_section_title(m.group(0))]
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
