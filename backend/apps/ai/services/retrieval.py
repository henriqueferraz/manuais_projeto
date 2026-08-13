"""Indexação de manuais e retrieval com filtro por metadados + similaridade."""

from __future__ import annotations

from dataclasses import dataclass

import structlog
from django.conf import settings
from django.db import connection, transaction
from django.db.models import Q

from apps.ai.models import ManualChunk
from apps.ai.services.chunking import chunk_manual_text
from apps.ai.services.embeddings import embed_query, embed_texts, hybrid_score
from apps.manuals.models import Manual
from apps.manuals.services.pdf_extract import extract_pdf_text
from apps.manuals.services.sanitize import sanitize_manual_text

logger = structlog.get_logger(__name__)


@dataclass(frozen=True)
class RetrievedChunk:
    """Chunk de manual com score híbrido (embedding + lexical)."""

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
    category_name: str = "",
    model_code: str = "",
    top_k: int | None = None,
    min_score: float | None = None,
) -> list[RetrievedChunk]:
    """Filtro por produto/categoria/modelo antes da similaridade coseno + lexical."""
    top_k = top_k or int(getattr(settings, "RAG_TOP_K", 4))
    min_score = (
        min_score if min_score is not None else float(getattr(settings, "RAG_MIN_SCORE", 0.12))
    )
    qs = ManualChunk.objects.select_related("manual", "product", "category")
    qs = _apply_product_scope(
        qs,
        product_id=product_id,
        category_id=category_id,
        category_name=category_name,
        model_code=model_code,
    )
    # Inclui tipo/modelo na query para reforçar lexical quando o filtro for amplo.
    scoped_query = query
    extras = [p for p in (category_name, model_code) if p]
    if extras:
        scoped_query = f"{query} {' '.join(extras)}".strip()

    query_vec = embed_query(scoped_query)
    hybrid_hits: list[RetrievedChunk] = []

    if connection.vendor == "postgresql" and getattr(settings, "USE_PGVECTOR", True):
        pg_hits = _retrieve_pgvector(
            query_vec,
            query=scoped_query,
            product_id=product_id,
            category_id=category_id,
            top_k=max(top_k * 3, 12),
            min_score=min_score,
        )
        # Lista vazia NÃO deve pular o fallback JSON: embedding_vec pode
        # estar NULL (sync falhou) enquanto `embedding` JSON ainda é útil.
        if pg_hits:
            hybrid_hits = pg_hits

    if not hybrid_hits:
        scored: list[RetrievedChunk] = []
        for chunk in qs.iterator(chunk_size=200):
            doc_text = f"{chunk.section or ''}\n{chunk.content or ''}".strip()
            score = hybrid_score(scoped_query, doc_text, query_vec, chunk.embedding or [])
            if score >= min_score:
                scored.append(RetrievedChunk(chunk=chunk, score=score))
        scored.sort(key=lambda item: item.score, reverse=True)
        hybrid_hits = scored

    # Sempre mescla lexical: títulos/receitas ("MILK SHAKE CREMOSO") podem
    # perder no embedding e nunca aparecer se o fallback só rodar com lista vazia.
    lexical_hits = _lexical_candidates(qs, scoped_query)
    return _merge_hits(hybrid_hits, lexical_hits, top_k=top_k, min_score=min_score)


def _apply_product_scope(
    qs,
    *,
    product_id: int | None,
    category_id: int | None,
    category_name: str = "",
    model_code: str = "",
):
    """Restringe chunks ao produto, categoria ou modelo informado pelo cliente."""
    if product_id:
        return qs.filter(product_id=product_id)
    if category_id:
        return qs.filter(category_id=category_id)

    filters = Q()
    name = (category_name or "").strip()
    code = (model_code or "").strip()
    if name:
        filters |= (
            Q(category__name__icontains=name)
            | Q(product__category__name__icontains=name)
            | Q(manual__linked_product__category__name__icontains=name)
        )
    if code:
        filters |= (
            Q(product__model_code__icontains=code)
            | Q(product__equipment_model__code__icontains=code)
            | Q(manual__linked_product__model_code__icontains=code)
            | Q(content__icontains=code)
            | Q(section__icontains=code)
        )
    if filters:
        return qs.filter(filters).distinct()
    return qs


def _lexical_candidates(qs, query: str) -> list[RetrievedChunk]:
    from apps.ai.services.embeddings import tokenize

    q_tokens = [t for t in tokenize(query) if len(t) > 2]
    # Ignora tokens muito genéricos para ranking lexical de receita/uso.
    skip = {"tem", "uma", "um", "receita", "modo", "para", "com", "como"}
    q_tokens = [t for t in q_tokens if t not in skip]
    if not q_tokens:
        return []

    hits: list[RetrievedChunk] = []
    for chunk in qs.iterator(chunk_size=200):
        doc = f"{chunk.section or ''}\n{chunk.content or ''}".lower()
        hits_n = sum(1 for t in q_tokens if t in doc)
        if hits_n < 1:
            continue
        # Frase contígua (ex.: "milk shake cremoso") recebe boost forte.
        phrase_bonus = 0.0
        for n in (3, 2):
            for i in range(0, max(0, len(q_tokens) - n + 1)):
                phrase = " ".join(q_tokens[i : i + n])
                if len(phrase) >= 7 and phrase in doc:
                    phrase_bonus = 0.35 if n >= 3 else 0.22
                    break
            if phrase_bonus:
                break
        score = min(0.95, 0.20 + 0.14 * hits_n + phrase_bonus)
        hits.append(RetrievedChunk(chunk=chunk, score=score))
    hits.sort(key=lambda item: item.score, reverse=True)
    return hits


def _merge_hits(
    *groups: list[RetrievedChunk],
    top_k: int,
    min_score: float,
) -> list[RetrievedChunk]:
    best: dict[int, RetrievedChunk] = {}
    for group in groups:
        for hit in group:
            if hit.score < min_score:
                continue
            prev = best.get(hit.chunk.pk)
            if prev is None or hit.score > prev.score:
                best[hit.chunk.pk] = hit
    merged = sorted(best.values(), key=lambda item: item.score, reverse=True)
    return merged[:top_k]


def _retrieve_pgvector(
    query_vec: list[float],
    *,
    query: str = "",
    product_id: int | None,
    category_id: int | None,
    top_k: int,
    min_score: float,
) -> list[RetrievedChunk] | None:
    if not _pgvector_ready():
        return None

    vec_literal = "[" + ",".join(str(float(v)) for v in query_vec) + "]"
    # Busca candidatos a mais e reordena com hybrid (seção + conteúdo).
    candidate_k = max(top_k * 5, 20)
    # where clauses são literais fixos + placeholders — não interpolam input do usuário
    if product_id:
        sql = (
            "SELECT id, 1 - (embedding_vec <=> %s::vector) AS score "
            "FROM ai_manualchunk "
            "WHERE embedding_vec IS NOT NULL AND product_id = %s "
            "ORDER BY embedding_vec <=> %s::vector LIMIT %s"
        )
        exec_params = [vec_literal, product_id, vec_literal, candidate_k]
    elif category_id:
        sql = (
            "SELECT id, 1 - (embedding_vec <=> %s::vector) AS score "
            "FROM ai_manualchunk "
            "WHERE embedding_vec IS NOT NULL AND category_id = %s "
            "ORDER BY embedding_vec <=> %s::vector LIMIT %s"
        )
        exec_params = [vec_literal, category_id, vec_literal, candidate_k]
    else:
        sql = (
            "SELECT id, 1 - (embedding_vec <=> %s::vector) AS score "
            "FROM ai_manualchunk "
            "WHERE embedding_vec IS NOT NULL "
            "ORDER BY embedding_vec <=> %s::vector LIMIT %s"
        )
        exec_params = [vec_literal, vec_literal, candidate_k]

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
    chunks = ManualChunk.objects.in_bulk(ids)
    results: list[RetrievedChunk] = []
    for chunk_id in ids:
        chunk = chunks.get(chunk_id)
        if not chunk:
            continue
        doc_text = f"{chunk.section or ''}\n{chunk.content or ''}".strip()
        score = hybrid_score(query, doc_text, query_vec, chunk.embedding or [])
        if score >= min_score:
            results.append(RetrievedChunk(chunk=chunk, score=score))
    results.sort(key=lambda item: item.score, reverse=True)
    return results[:top_k]


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
    # Savepoint: falha de DDL no Postgres aborta a TX; sem atomic o erro
    # contaminaria a transação chamadora mesmo após o except.
    try:
        with transaction.atomic():
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
