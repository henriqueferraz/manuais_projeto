"""Serviços de upload, pipeline e revisão humana (HITL)."""

from __future__ import annotations

from decimal import Decimal

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
from apps.manuals.services.pdf_extract import extract_pdf_text
from apps.manuals.services.sanitize import sanitize_manual_text
from apps.manuals.services.structure import dump_product_json, structure_manual_text
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
    """Pipeline: ler PDF → sanitizar → estruturar → awaiting_review."""
    log = ExtractionLog.objects.select_related("manual").get(pk=extraction_id)
    log.mark_running()
    manual = log.manual

    try:
        content = manual.file.read()
        if hasattr(manual.file, "seek"):
            manual.file.seek(0)

        pdf = extract_pdf_text(content)
        cleaned = sanitize_manual_text(pdf.text)
        log.raw_text_preview = cleaned[:4000]

        if len(cleaned) < 40:
            raise ValueError(
                "Texto insuficiente no PDF (possível scan sem OCR). "
                "Habilite MANUAL_OCR_ENABLED ou envie PDF com texto."
            )

        result = structure_manual_text(
            cleaned,
            manufacturer_hint=manual.manufacturer,
            filename=manual.original_filename,
        )
        product_data = dump_product_json(result.product)

        log.raw_json = product_data
        log.model_name = result.model_name
        log.tokens_in = result.tokens_in
        log.tokens_out = result.tokens_out
        log.cost_estimate = Decimal(str(result.cost_estimate))
        log.confidence = result.product.confidence
        log.langsmith_trace_id = result.langsmith_trace_id
        log.prompt_version = result.prompt_version
        log.status = ExtractionLog.Status.AWAITING_REVIEW
        log.finished_at = timezone.now()
        log.error_message = ""
        log.save()

        if not manual.manufacturer and result.product.manufacturer:
            manual.manufacturer = result.product.manufacturer
            manual.save(update_fields=["manufacturer", "updated_at"])

        logger.info(
            "extraction_ok",
            extraction_id=log.pk,
            confidence=log.confidence,
            cost=float(log.cost_estimate),
            tokens_in=log.tokens_in,
            tokens_out=log.tokens_out,
        )
        return log
    except Exception as exc:  # noqa: BLE001
        logger.exception("extraction_failed", extraction_id=log.pk)
        log.mark_failed(str(exc))
        return log


@transaction.atomic
def approve_extraction(
    log: ExtractionLog,
    *,
    reviewer: AbstractBaseUser,
    corrected: dict | None = None,
    notes: str = "",
) -> Product:
    """HITL: cria/atualiza Product como rascunho — nunca publica automaticamente."""
    if log.status not in {
        ExtractionLog.Status.AWAITING_REVIEW,
        ExtractionLog.Status.REJECTED,
    }:
        raise ValueError(f"Extração em status inválido para aprovação: {log.status}")

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
    return product


@transaction.atomic
def reject_extraction(
    log: ExtractionLog,
    *,
    reviewer: AbstractBaseUser,
    notes: str = "",
) -> ExtractionLog:
    if log.status not in {
        ExtractionLog.Status.AWAITING_REVIEW,
        ExtractionLog.Status.APPROVED,
    }:
        raise ValueError(f"Extração em status inválido para rejeição: {log.status}")

    log.status = ExtractionLog.Status.REJECTED
    log.reviewed_by = reviewer
    log.reviewed_at = timezone.now()
    log.review_notes = notes
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
