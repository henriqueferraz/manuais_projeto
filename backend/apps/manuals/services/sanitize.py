"""Sanitização anti prompt-injection via conteúdo de PDF."""

from __future__ import annotations

import re

# Padrões típicos de instruções embutidas em documentos maliciosos
_INJECTION_PATTERNS = [
    re.compile(r"(?i)ignore\s+(all\s+)?(previous|prior|above)\s+instructions?"),
    re.compile(r"(?i)disregard\s+(all\s+)?(previous|prior)\s+"),
    re.compile(r"(?i)system\s*:\s*"),
    re.compile(r"(?i)</?\s*system\s*>"),
    re.compile(r"(?i)you\s+are\s+now\s+"),
    re.compile(r"(?i)new\s+instructions?\s*:"),
    re.compile(r"(?i)\[\s*INST\s*\]"),
    re.compile(r"(?i)do\s+not\s+follow\s+the\s+developer"),
]


def sanitize_manual_text(text: str, *, max_chars: int = 80_000) -> str:
    """
    Remove/neutraliza tentativas de prompt injection e limita tamanho.
    Conteúdo do manual NÃO é instrução — só dado a extrair.
    """
    if not text:
        return ""

    cleaned = text.replace("\x00", " ")
    # Normaliza whitespace excessivo mantendo quebras de linha úteis
    cleaned = re.sub(r"[ \t]+\n", "\n", cleaned)
    cleaned = re.sub(r"\n{4,}", "\n\n\n", cleaned)

    for pattern in _INJECTION_PATTERNS:
        cleaned = pattern.sub("[CONTEUDO_REMOVIDO]", cleaned)

    if len(cleaned) > max_chars:
        cleaned = cleaned[:max_chars] + "\n\n[...texto truncado para limite de tokens...]"

    return cleaned.strip()
