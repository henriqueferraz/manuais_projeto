"""Serviços de upload, pipeline e revisão humana (HITL)."""

from __future__ import annotations

import structlog
from django.contrib.auth.models import AbstractBaseUser
from django.core.files.base import ContentFile
from django.db import transaction
from django.utils import timezone
from django.utils.text import slugify

from apps.accounts.models import SensitiveActionLog
from apps.catalog.models import Category
from apps.manuals.models import ExtractionLog, Manual
from apps.manuals.schemas import ExtractedProduct
from apps.manuals.services.structure import dump_product_json
from apps.manuals.validators import validate_manual_upload
from apps.products.models import Product, ProductTranslation

logger = structlog.get_logger(__name__)


def create_manual_from_upload(
    *,
    content: bytes,
    filename: str,
    user: AbstractBaseUser | None = None,
    manufacturer: str = "",
    source_locale: str = "pt-BR",
    enqueue: bool = True,
) -> tuple[Manual, ExtractionLog]:
    """Valida, grava Manual no storage, cria ExtractionLog e enfileira task."""
    validated = validate_manual_upload(content, filename)

    manual = Manual(
        original_filename=validated.filename,
        mime_type=validated.mime_type,
        manufacturer=manufacturer,
        source_locale=source_locale,
        uploaded_by=user if getattr(user, "is_authenticated", False) else None,
        scan_status=validated.scan_status,
    )
    manual.compute_and_set_sha256(validated.content)
    manual.file.save(validated.filename, ContentFile(validated.content), save=False)
    manual.save()

    log = ExtractionLog.objects.create(
        manual=manual,
        status=ExtractionLog.Status.PENDING,
    )

    SensitiveActionLog.objects.create(
        action=SensitiveActionLog.Action.OTHER,
        actor=user if getattr(user, "is_authenticated", False) else None,
        object_repr=f"Manual upload: {manual.original_filename}",
        details={"manual_id": manual.pk, "sha256": manual.sha256, "size": manual.size_bytes},
    )

    if enqueue:
        from apps.manuals.tasks import extract_manual_task

        extract_manual_task.delay(log.pk)

    logger.info("manual_uploaded", manual_id=manual.pk, extraction_id=log.pk)
    return manual, log


def run_extraction(extraction_id: int) -> ExtractionLog:
    """Pipeline LangGraph: PDF → estrutura → interrupt HITL (awaiting_review)."""
    from apps.manuals.graphs.extraction import run_extraction_graph

    try:
        return run_extraction_graph(extraction_id)
    except Exception as exc:  # noqa: BLE001
        log = ExtractionLog.objects.filter(pk=extraction_id).first()
        if log is None:
            raise
        if log.status == ExtractionLog.Status.AWAITING_REVIEW:
            return log
        logger.exception("extraction_failed", extraction_id=extraction_id)
        if log.status != ExtractionLog.Status.FAILED:
            log.mark_failed(str(exc))
        return log


def apply_review_decision(
    log: ExtractionLog,
    *,
    action: str,
    reviewer_id: int | None,
    corrected: dict | None = None,
    notes: str = "",
):
    """Aplica approve/reject após retomada do grafo (ou fallback sem checkpoint)."""
    from django.contrib.auth import get_user_model

    User = get_user_model()
    reviewer = User.objects.filter(pk=reviewer_id).first() if reviewer_id else None
    if reviewer is None:
        raise ValueError("Revisor obrigatório para finalizar a extração.")

    if action == "reject":
        return reject_extraction(log, reviewer=reviewer, notes=notes, skip_graph_resume=True)
    return approve_extraction(
        log,
        reviewer=reviewer,
        corrected=corrected,
        notes=notes,
        skip_graph_resume=True,
    )


@transaction.atomic
def approve_extraction(
    log: ExtractionLog,
    *,
    reviewer: AbstractBaseUser,
    corrected: dict | None = None,
    notes: str = "",
    skip_graph_resume: bool = False,
) -> Product:
    """HITL: cria/atualiza Product como rascunho — nunca publica automaticamente."""
    if log.status not in {
        ExtractionLog.Status.AWAITING_REVIEW,
        ExtractionLog.Status.REJECTED,
    }:
        raise ValueError(f"Extração em status inválido para aprovação: {log.status}")

    # Retoma grafo LangGraph se pausado (não reinicia extract/structure).
    # MemorySaver some entre processos/reloads — fallback para approve direto.
    # Savepoint: falha no resume não aborta a transação externa (Postgres).
    if not skip_graph_resume and log.langgraph_interrupted and log.langgraph_thread_id:
        from apps.manuals.graphs.extraction import resume_extraction_graph

        try:
            with transaction.atomic():
                resume_extraction_graph(
                    log.pk,
                    action="approve",
                    reviewer_id=getattr(reviewer, "pk", None),
                    corrected=corrected,
                    notes=notes,
                )
                log.refresh_from_db()
                if log.status == ExtractionLog.Status.APPROVED and log.draft_product_id:
                    return log.draft_product
        except Exception:  # noqa: BLE001
            logger.warning(
                "langgraph_resume_failed_fallback",
                extraction_id=log.pk,
                thread_id=log.langgraph_thread_id,
                exc_info=True,
            )
            log.refresh_from_db()

        # Resume sem checkpoint válido pode deixar status inconsistente.
        if log.status == ExtractionLog.Status.APPROVED and log.draft_product_id:
            return log.draft_product

    data = corrected if corrected is not None else (log.corrected_json or log.raw_json)
    product_schema = ExtractedProduct.model_validate(data)

    category = _resolve_category(product_schema.category_hint)
    sku = product_schema.sku_suggestion or f"DRAFT-{log.pk}-{product_schema.model_code}"
    sku = sku[:64]

    product = log.draft_product
    if product is None:
        # Garante SKU único
        base_sku = sku
        n = 1
        while Product.objects.filter(sku=sku).exists():
            sku = f"{base_sku}-{n}"[:64]
            n += 1
        product = Product(
            sku=sku,
            status=Product.Status.DRAFT,
            product_kind=product_schema.product_kind,
            category=category,
            brand=product_schema.brand,
            model_code=product_schema.model_code,
            voltage=product_schema.voltage,
            power_w=product_schema.power_w,
            weight_kg=product_schema.weight_kg,
            dimensions=product_schema.dimensions or {},
            specs=product_schema.specs or {},
            manual=log.manual,
            extraction_confidence=product_schema.confidence,
            price=0,
        )
        product.save()
    else:
        product.status = Product.Status.DRAFT
        product.brand = product_schema.brand
        product.model_code = product_schema.model_code
        product.voltage = product_schema.voltage
        product.power_w = product_schema.power_w
        product.weight_kg = product_schema.weight_kg
        product.dimensions = product_schema.dimensions or {}
        product.specs = product_schema.specs or {}
        product.extraction_confidence = product_schema.confidence
        product.category = category or product.category
        product.manual = log.manual
        product.published_at = None
        product.save()

    ProductTranslation.objects.update_or_create(
        product=product,
        locale="pt-BR",
        defaults={
            "name": product_schema.name,
            "description": product_schema.description,
            "slug": slugify(product_schema.name)[:180],
        },
    )

    log.corrected_json = dump_product_json(product_schema)
    log.status = ExtractionLog.Status.APPROVED
    log.reviewed_by = reviewer
    log.reviewed_at = timezone.now()
    log.review_notes = notes
    log.draft_product = product
    log.langgraph_interrupted = False
    log.save()

    log.manual.linked_product = product
    log.manual.save(update_fields=["linked_product", "updated_at"])

    SensitiveActionLog.objects.create(
        action=SensitiveActionLog.Action.OTHER,
        actor=reviewer,
        object_repr=f"Aprovou extração #{log.pk} → draft {product.sku}",
        details={
            "extraction_id": log.pk,
            "product_id": product.pk,
            "status": product.status,
        },
    )

    # F5: indexar após commit — evita DDL/embed abortar a TX do approve (Postgres).
    manual_id = log.manual_id

    def _enqueue_index() -> None:
        from apps.ai.tasks import index_manual_task

        index_manual_task.delay(manual_id)

    transaction.on_commit(_enqueue_index)
    return product


@transaction.atomic
def reject_extraction(
    log: ExtractionLog,
    *,
    reviewer: AbstractBaseUser,
    notes: str = "",
    skip_graph_resume: bool = False,
) -> ExtractionLog:
    if log.status not in {
        ExtractionLog.Status.AWAITING_REVIEW,
        ExtractionLog.Status.APPROVED,
    }:
        raise ValueError(f"Extração em status inválido para rejeição: {log.status}")

    if not skip_graph_resume and log.langgraph_interrupted and log.langgraph_thread_id:
        from apps.manuals.graphs.extraction import resume_extraction_graph

        try:
            with transaction.atomic():
                resume_extraction_graph(
                    log.pk,
                    action="reject",
                    reviewer_id=getattr(reviewer, "pk", None),
                    notes=notes,
                )
                log.refresh_from_db()
                if log.status == ExtractionLog.Status.REJECTED:
                    return log
        except Exception:  # noqa: BLE001
            logger.exception("extraction_graph_resume_reject_fallback", extraction_id=log.pk)
            log.refresh_from_db()

    log.status = ExtractionLog.Status.REJECTED
    log.reviewed_by = reviewer
    log.reviewed_at = timezone.now()
    log.review_notes = notes
    log.langgraph_interrupted = False
    log.save()

    if log.draft_product_id:
        product = log.draft_product
        product.status = Product.Status.DRAFT
        product.published_at = None
        product.save(update_fields=["status", "published_at", "updated_at"])

    SensitiveActionLog.objects.create(
        action=SensitiveActionLog.Action.OTHER,
        actor=reviewer,
        object_repr=f"Rejeitou extração #{log.pk}",
        details={"extraction_id": log.pk, "notes": notes[:500]},
    )
    return log


def _resolve_category(hint: str) -> Category | None:
    if not hint:
        return None
    slug = slugify(hint)[:140]
    category, _ = Category.objects.get_or_create(
        slug=slug,
        defaults={"name": hint.replace("-", " ").title()},
    )
    return category
