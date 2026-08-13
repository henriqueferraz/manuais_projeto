"""Embeddings para RAG — mock determinístico (CI) ou OpenAI."""

from __future__ import annotations

import hashlib
import math
import re
import struct

import structlog
from django.conf import settings

logger = structlog.get_logger(__name__)

_TOKEN_RE = re.compile(r"[a-zA-ZÀ-ÿ0-9.]{2,}")


def embed_texts(texts: list[str]) -> list[list[float]]:
    mode = getattr(settings, "EMBEDDING_MODE", "mock").lower()
    if mode == "openai":
        return _embed_openai(texts)
    return [_embed_mock(t) for t in texts]


def embed_query(text: str) -> list[float]:
    return embed_texts([text])[0]


def tokenize(text: str) -> set[str]:
    return {t.lower() for t in _TOKEN_RE.findall(text or "")}


def lexical_overlap(query: str, document: str) -> float:
    """Jaccard simples — reforça retrieval no modo mock."""
    q = tokenize(query)
    d = tokenize(document)
    if not q or not d:
        return 0.0
    inter = len(q & d)
    union = len(q | d)
    return inter / union if union else 0.0


def cosine_similarity(a: list[float], b: list[float]) -> float:
    if not a or not b or len(a) != len(b):
        return 0.0
    dot = 0.0
    na = 0.0
    nb = 0.0
    for x, y in zip(a, b, strict=True):
        dot += x * y
        na += x * x
        nb += y * y
    if na <= 0 or nb <= 0:
        return 0.0
    return dot / math.sqrt(na * nb)


def hybrid_score(
    query: str,
    document: str,
    query_vec: list[float],
    doc_vec: list[float],
) -> float:
    """Combina similaridade coseno com overlap lexical."""
    cos = cosine_similarity(query_vec, doc_vec)
    lex = lexical_overlap(query, document)
    mode = getattr(settings, "EMBEDDING_MODE", "mock").lower()
    if mode == "mock":
        return 0.35 * cos + 0.65 * lex
    # OpenAI: mais peso lexical para títulos/receitas (ex.: "massa para pizza").
    return 0.55 * cos + 0.45 * lex


def _embed_mock(text: str) -> list[float]:
    """Vetor determinístico (hash + boost por token) para CI/local."""
    dims = int(getattr(settings, "EMBEDDING_DIMS", 64))
    digest = hashlib.sha256((text or "").encode("utf-8")).digest()
    values: list[float] = []
    seed = digest
    while len(values) < dims:
        seed = hashlib.sha256(seed).digest()
        for i in range(0, len(seed), 4):
            if len(values) >= dims:
                break
            raw = struct.unpack_from(">I", seed, i)[0]
            values.append((raw / 2**32) * 2.0 - 1.0)

    tokens = tokenize(text)
    for i, token in enumerate(sorted(tokens)[: dims // 2]):
        h = int(hashlib.md5(token.encode(), usedforsecurity=False).hexdigest()[:8], 16)
        idx = h % dims
        values[idx] = min(1.0, values[idx] + 0.45 + (i % 5) * 0.02)

    return _l2_normalize(values)


def _embed_openai(texts: list[str]) -> list[list[float]]:
    from langchain_openai import OpenAIEmbeddings

    model = getattr(settings, "OPENAI_EMBEDDING_MODEL", "text-embedding-3-small")
    dims = int(getattr(settings, "EMBEDDING_DIMS", 1536))
    emb = OpenAIEmbeddings(
        model=model,
        api_key=settings.OPENAI_API_KEY or None,
        dimensions=dims if "text-embedding-3" in model else None,
    )
    vectors = emb.embed_documents(texts)
    logger.info("openai_embeddings", count=len(texts), dims=len(vectors[0]) if vectors else 0)
    return vectors


def _l2_normalize(values: list[float]) -> list[float]:
    norm = math.sqrt(sum(v * v for v in values)) or 1.0
    return [v / norm for v in values]
