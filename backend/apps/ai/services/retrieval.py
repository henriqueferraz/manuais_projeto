"""Indexação de manuais e retrieval com filtro por metadados + similaridade."""

from __future__ import annotations

from dataclasses import dataclass

import structlog
from django.conf import settings
from django.db import connection, transaction

from apps.ai.models import ManualChunk
from apps.ai.services.chunking import chunk_manual_text
from apps.ai.services.embeddings import embed_query, embed_texts, hybrid_score
from apps.manuals.models import Manual
from apps.manuals.services.pdf_extract import extract_pdf_text
from apps.manuals.services.sanitize import sanitize_manual_text

logger = structlog.get_logger(__name__)


@dataclass(frozen=True)
class RetrievedChunk:
    chunk: ManualChunk
    score: float


def index_manual(manual_id: int, *, text: str | None = None) -> int:
    """
    Chunk + embed + persiste ManualChunk.
    Em Postgres com pgvector, sincroniza coluna embedding_vec + índice HNSW.
    """
    manual = Manual.objects.select_related("linked_product", "linked_product__category").get(
        pk=manual_id
    )
    source_text = text
    if not source_text:
        content = manual.file.read()
        if hasattr(manual.file, "seek"):
            manual.file.seek(0)
        pdf = extract_pdf_text(content)
        source_text = sanitize_manual_text(pdf.text)

    chunks = chunk_manual_text(source_text)
    if not chunks:
        ManualChunk.objects.filter(manual=manual).delete()
        logger.warning("index_manual_empty", manual_id=manual_id)
        return 0

    vectors = embed_texts([c.content for c in chunks])
    product = manual.linked_product
    category = product.category if product else None

    with transaction.atomic():
        ManualChunk.objects.filter(manual=manual).delete()
        objs = [
            ManualChunk(
                manual=manual,
                product=product,
                category=category,
                content=chunk.content,
                section=chunk.section,
                page=chunk.page,
                chunk_index=chunk.chunk_index,
                embedding=vector,
                embedding_dims=len(vector),
                metadata=chunk.metadata,
            )
            for chunk, vector in zip(chunks, vectors, strict=True)
        ]
        ManualChunk.objects.bulk_create(objs, batch_size=100)

    created = ManualChunk.objects.filter(manual=manual).count()
    _sync_pgvector(manual_id)
    logger.info("index_manual_ok", manual_id=manual_id, chunks=created)
    return created


def retrieve(
    query: str,
    *,
    product_id: int | None = None,
    category_id: int | None = None,
    top_k: int | None = None,
    min_score: float | None = None,
) -> list[RetrievedChunk]:
    """Filtro por produto/categoria antes da similaridade coseno."""
    top_k = top_k or int(getattr(settings, "RAG_TOP_K", 4))
    min_score = (
        min_score if min_score is not None else float(getattr(settings, "RAG_MIN_SCORE", 0.12))
    )
    qs = ManualChunk.objects.select_related("manual", "product", "category")
    if product_id:
        qs = qs.filter(product_id=product_id)
    elif category_id:
        qs = qs.filter(category_id=category_id)

    query_vec = embed_query(query)

    if connection.vendor == "postgresql" and getattr(settings, "USE_PGVECTOR", True):
        pg_hits = _retrieve_pgvector(
            query_vec,
            product_id=product_id,
            category_id=category_id,
            top_k=top_k,
            min_score=min_score,
        )
        # Lista vazia NÃO deve pular o fallback JSON: embedding_vec pode
        # estar NULL (sync falhou) enquanto `embedding` JSON ainda é útil.
        if pg_hits:
            return pg_hits

    scored: list[RetrievedChunk] = []
    for chunk in qs.iterator(chunk_size=200):
        score = hybrid_score(query, chunk.content, query_vec, chunk.embedding or [])
        if score >= min_score:
            scored.append(RetrievedChunk(chunk=chunk, score=score))
    scored.sort(key=lambda item: item.score, reverse=True)
    if scored:
        return scored[:top_k]

    # Fallback lexical: contém tokens significativos da pergunta
    from apps.ai.services.embeddings import tokenize

    q_tokens = {t for t in tokenize(query) if len(t) > 3}
    if not q_tokens:
        return []
    fallback: list[RetrievedChunk] = []
    for chunk in qs.iterator(chunk_size=200):
        content_l = chunk.content.lower()
        hits_n = sum(1 for t in q_tokens if t in content_l)
        if hits_n:
            fallback.append(RetrievedChunk(chunk=chunk, score=0.15 + 0.1 * hits_n))
    fallback.sort(key=lambda item: item.score, reverse=True)
    return fallback[:top_k]


def _retrieve_pgvector(
    query_vec: list[float],
    *,
    product_id: int | None,
    category_id: int | None,
    top_k: int,
    min_score: float,
) -> list[RetrievedChunk] | None:
    if not _pgvector_ready():
        return None

    filters = ["embedding_vec IS NOT NULL"]
    params: list = []
    if product_id:
        filters.append("product_id = %s")
        params.append(product_id)
    elif category_id:
        filters.append("category_id = %s")
        params.append(category_id)

    vec_literal = "[" + ",".join(str(float(v)) for v in query_vec) + "]"
    # where clauses são literais fixos + placeholders — não interpolam input do usuário
    if product_id:
        sql = (
            "SELECT id, 1 - (embedding_vec <=> %s::vector) AS score "
            "FROM ai_manualchunk "
            "WHERE embedding_vec IS NOT NULL AND product_id = %s "
            "ORDER BY embedding_vec <=> %s::vector LIMIT %s"
        )
        exec_params = [vec_literal, product_id, vec_literal, top_k]
    elif category_id:
        sql = (
            "SELECT id, 1 - (embedding_vec <=> %s::vector) AS score "
            "FROM ai_manualchunk "
            "WHERE embedding_vec IS NOT NULL AND category_id = %s "
            "ORDER BY embedding_vec <=> %s::vector LIMIT %s"
        )
        exec_params = [vec_literal, category_id, vec_literal, top_k]
    else:
        sql = (
            "SELECT id, 1 - (embedding_vec <=> %s::vector) AS score "
            "FROM ai_manualchunk "
            "WHERE embedding_vec IS NOT NULL "
            "ORDER BY embedding_vec <=> %s::vector LIMIT %s"
        )
        exec_params = [vec_literal, vec_literal, top_k]

    try:
        with connection.cursor() as cursor:
            cursor.execute(sql, exec_params)
            rows = cursor.fetchall()
    except Exception as exc:  # noqa: BLE001
        logger.warning("pgvector_retrieve_failed", error=str(exc))
        return None

    if not rows:
        return []

    ids = [row[0] for row in rows]
    scores = {row[0]: float(row[1]) for row in rows}
    chunks = ManualChunk.objects.in_bulk(ids)
    results: list[RetrievedChunk] = []
    for chunk_id in ids:
        chunk = chunks.get(chunk_id)
        if not chunk:
            continue
        score = scores[chunk_id]
        if score >= min_score:
            results.append(RetrievedChunk(chunk=chunk, score=score))
    return results


def _sync_pgvector(manual_id: int) -> None:
    if connection.vendor != "postgresql" or not getattr(settings, "USE_PGVECTOR", True):
        return
    if not _ensure_pgvector_schema():
        return
    with connection.cursor() as cursor:
        cursor.execute(
            """
            UPDATE ai_manualchunk AS c
            SET embedding_vec = (
                SELECT (('[' || string_agg(elem, ',') || ']')::vector)
                FROM jsonb_array_elements_text(to_jsonb(c.embedding)) AS elem
            )
            WHERE c.manual_id = %s
              AND c.embedding IS NOT NULL
            """,
            [manual_id],
        )


def _ensure_pgvector_schema() -> bool:
    try:
        with connection.cursor() as cursor:
            cursor.execute("CREATE EXTENSION IF NOT EXISTS vector")
            cursor.execute("""
                ALTER TABLE ai_manualchunk
                ADD COLUMN IF NOT EXISTS embedding_vec vector
                """)
            cursor.execute("""
                DO $$
                BEGIN
                  IF NOT EXISTS (
                    SELECT 1 FROM pg_indexes WHERE indexname = 'ai_manualchunk_embedding_hnsw'
                  ) THEN
                    BEGIN
                      CREATE INDEX ai_manualchunk_embedding_hnsw
                      ON ai_manualchunk
                      USING hnsw (embedding_vec vector_cosine_ops);
                    EXCEPTION WHEN others THEN
                      NULL;
                    END;
                  END IF;
                END$$;
                """)
        return True
    except Exception as exc:  # noqa: BLE001
        logger.warning("pgvector_schema_failed", error=str(exc))
        return False


def _pgvector_ready() -> bool:
    try:
        with connection.cursor() as cursor:
            cursor.execute("""
                SELECT 1
                FROM information_schema.columns
                WHERE table_name = 'ai_manualchunk'
                  AND column_name = 'embedding_vec'
                """)
            return cursor.fetchone() is not None
    except Exception:  # noqa: BLE001
        return False
