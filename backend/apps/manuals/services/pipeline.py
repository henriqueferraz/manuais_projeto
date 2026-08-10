"""Serviços de upload, pipeline e revisão humana (HITL)."""

from __future__ import annotations

import re
from decimal import Decimal, InvalidOperation
from typing import Any

import structlog
from django.contrib.auth.models import AbstractBaseUser
from django.core.files.base import ContentFile
from django.db import transaction
from django.utils import timezone
from django.utils.text import slugify

from apps.accounts.models import SensitiveActionLog
from apps.catalog.models import Category
from apps.compatibility.models import Compatibility
from apps.manuals.models import ExtractionLog, Manual
from apps.manuals.schemas import ExtractedProduct, RelatedPartHint
from apps.manuals.services.structure import dump_product_json
from apps.manuals.validators import validate_manual_upload
from apps.products.models import Product, ProductTranslation

logger = structlog.get_logger(__name__)

# Campos do ExtractedProduct que não têm coluna em Product — vão para specs
_ORPHAN_SPEC_KEYS = (
    "frequency_hz",
    "consumption_kwh",
    "capacity",
    "ean",
    "barcode",
    "ncm_classification",
    "packaging_qty",
    "source_doc_types",
    "model_variants",
    "warranty",
    "certifications",
    "document_conflicts",
    "notes",
    "low_confidence_fields",
    "installation_requirements",
    "safety_warnings",
    "key_usage_steps",
    "manufacturer",
)

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

    category = _resolve_category(
        product_schema.category or product_schema.category_hint
    )
    sku = product_schema.sku_suggestion or f"DRAFT-{log.pk}-{product_schema.model_code}"
    sku = sku[:64]
    dimensions = product_schema.dimensions_mm or product_schema.dimensions or {}
    specs = _merge_product_specs(product_schema)

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
            dimensions=dimensions,
            specs=specs,
            manual=log.manual,
            extraction_confidence=product_schema.confidence,
            price=0,
        )
        product.save()
    else:
        product.status = Product.Status.DRAFT
        product.product_kind = product_schema.product_kind
        product.brand = product_schema.brand
        product.model_code = product_schema.model_code
        product.voltage = product_schema.voltage
        product.power_w = product_schema.power_w
        product.weight_kg = product_schema.weight_kg
        product.dimensions = dimensions
        product.specs = specs
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

    materialized = _materialize_related_parts(product, product_schema)

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
            "parts_created": materialized["created"],
            "parts_reused": materialized["reused"],
            "compatibilities": materialized["compatibilities"],
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


def _merge_product_specs(schema: ExtractedProduct) -> dict[str, Any]:
    """Combina specs livres do LLM com campos órfãos do schema v2."""
    specs: dict[str, Any] = dict(schema.specs or {})
    data = schema.model_dump()
    for key in _ORPHAN_SPEC_KEYS:
        value = data.get(key)
        if value in (None, "", [], {}):
            continue
        if key == "warranty" and isinstance(value, dict):
            if not any(v is not None and v != "" for v in value.values()):
                continue
        specs[key] = value
    if schema.troubleshooting:
        specs["troubleshooting"] = [
            t.model_dump() if hasattr(t, "model_dump") else t
            for t in schema.troubleshooting
        ]
    if schema.assembly_summary is not None:
        dumped = schema.assembly_summary.model_dump()
        if any(dumped.get(k) for k in ("total_steps", "tools_required", "hardware_list")):
            specs["assembly_summary"] = dumped
    return specs


def _materialize_related_parts(
    parent: Product,
    schema: ExtractedProduct,
) -> dict[str, int]:
    """
    Cria Product(spare_part) draft + Compatibility para itens vendáveis.

    Itens com sellable_separately=false (ou sem code) ficam só no JSON do log.
    """
    created = reused = compatibilities = 0
    items: list[RelatedPartHint] = list(schema.spare_parts) + list(schema.accessories)

    for part in items:
        code = (part.code or "").strip()
        if not part.sellable_separately or not code:
            continue

        part_product, was_created = _get_or_create_part_product(parent, schema, part)
        if was_created:
            created += 1
        else:
            reused += 1

        models = part.compatible_with or [parent.model_code]
        if parent.model_code and parent.model_code not in models:
            models = [parent.model_code, *models]

        bom_notes = _bom_notes(part)
        for model_code in models:
            model_code = str(model_code).strip()
            if not model_code:
                continue
            _, created_compat = Compatibility.objects.get_or_create(
                equipment_brand=parent.brand[:120],
                equipment_model=model_code[:120],
                part_product=part_product,
                defaults={"notes": bom_notes[:255]},
            )
            if created_compat:
                compatibilities += 1
            elif bom_notes and not Compatibility.objects.filter(
                equipment_brand=parent.brand[:120],
                equipment_model=model_code[:120],
                part_product=part_product,
                notes=bom_notes[:255],
            ).exists():
                Compatibility.objects.filter(
                    equipment_brand=parent.brand[:120],
                    equipment_model=model_code[:120],
                    part_product=part_product,
                ).update(notes=bom_notes[:255])

    logger.info(
        "parts_materialized",
        parent_sku=parent.sku,
        created=created,
        reused=reused,
        compatibilities=compatibilities,
    )
    return {
        "created": created,
        "reused": reused,
        "compatibilities": compatibilities,
    }


def _get_or_create_part_product(
    parent: Product,
    schema: ExtractedProduct,
    part: RelatedPartHint,
) -> tuple[Product, bool]:
    code = (part.code or "").strip()
    brand = (schema.brand or parent.brand or "XX")[:120]
    sku = (part.sku_suggestion or f"{_sku_brand(brand)}-{code}")[:64]
    sku = re.sub(r"\s+", "-", sku).strip("-") or f"PART-{code}"[:64]

    existing = Product.objects.filter(sku=sku).first()
    if existing is None:
        existing = Product.objects.filter(
            brand=brand,
            model_code=code,
            product_kind=Product.Kind.SPARE_PART,
        ).first()

    category = _resolve_category(part.category) if part.category else None
    price = _coerce_price(part.unit_price)
    part_specs: dict[str, Any] = {
        "part_code": code,
        "ref_number": part.ref_number or "",
        "qty_per_unit": part.qty_per_unit,
        "parent_sku": parent.sku,
        "parent_model_code": parent.model_code,
    }
    if part.ean:
        part_specs["ean"] = part.ean
    if part.ncm_classification:
        part_specs["ncm_classification"] = part.ncm_classification
    if part.notes:
        part_specs["notes"] = part.notes

    name = (part.name or part.description or f"Peça {code}")[:200]
    description = (part.description or part.name or "")[:2000]

    if existing is not None:
        existing.product_kind = Product.Kind.SPARE_PART
        existing.brand = brand
        existing.model_code = code[:120]
        existing.status = Product.Status.DRAFT
        existing.published_at = None
        if category:
            existing.category = category
        if price is not None and existing.price == 0:
            existing.price = price
        merged = dict(existing.specs or {})
        merged.update({k: v for k, v in part_specs.items() if v not in (None, "")})
        existing.specs = merged
        if parent.manual_id and not existing.manual_id:
            existing.manual = parent.manual
        existing.save()
        ProductTranslation.objects.update_or_create(
            product=existing,
            locale="pt-BR",
            defaults={
                "name": name,
                "description": description,
                "slug": slugify(name)[:180] or slugify(sku)[:180],
            },
        )
        return existing, False

    base_sku = sku
    n = 1
    while Product.objects.filter(sku=sku).exists():
        sku = f"{base_sku}-{n}"[:64]
        n += 1

    product = Product(
        sku=sku,
        status=Product.Status.DRAFT,
        product_kind=Product.Kind.SPARE_PART,
        category=category,
        brand=brand,
        model_code=code[:120],
        price=price if price is not None else Decimal("0"),
        specs=part_specs,
        manual=parent.manual,
        extraction_confidence=schema.confidence,
    )
    product.save()
    ProductTranslation.objects.create(
        product=product,
        locale="pt-BR",
        name=name,
        description=description,
        slug=slugify(name)[:180] or slugify(sku)[:180],
    )
    return product, True


def _bom_notes(part: RelatedPartHint) -> str:
    bits: list[str] = []
    if part.ref_number:
        bits.append(f"ref={part.ref_number}")
    if part.qty_per_unit is not None and part.qty_per_unit != "":
        bits.append(f"qty={part.qty_per_unit}")
    return "; ".join(bits)


def _sku_brand(brand: str) -> str:
    return re.sub(r"[^A-Z0-9]", "", (brand or "XX").upper())[:6] or "XX"


def _coerce_price(value: float | None) -> Decimal | None:
    if value is None:
        return None
    try:
        return Decimal(str(value)).quantize(Decimal("0.01"))
    except (InvalidOperation, ValueError):
        return None


def extraction_review_summary(data: dict | ExtractedProduct | None) -> dict[str, Any]:
    """Resumo para badges da UI HITL."""
    empty = {
        "sellable_parts": 0,
        "composition_only": 0,
        "source_doc_types": [],
        "low_confidence_fields": [],
        "document_conflicts": 0,
    }
    if not data:
        return empty
    try:
        schema = (
            data
            if isinstance(data, ExtractedProduct)
            else ExtractedProduct.model_validate(data)
        )
    except Exception:  # noqa: BLE001
        # JSON parcial na UI — conta o que der
        parts = list(data.get("spare_parts") or []) + list(data.get("accessories") or [])
        sellable = 0
        composition = 0
        for p in parts:
            code = str((p or {}).get("code") or (p or {}).get("part_code") or "").strip()
            sellable_flag = (p or {}).get("sellable_separately", bool(code))
            if sellable_flag and code:
                sellable += 1
            else:
                composition += 1
        return {
            "sellable_parts": sellable,
            "composition_only": composition,
            "source_doc_types": list(data.get("source_doc_types") or []),
            "low_confidence_fields": list(data.get("low_confidence_fields") or []),
            "document_conflicts": len(data.get("document_conflicts") or []),
        }

    items = list(schema.spare_parts) + list(schema.accessories)
    sellable = sum(1 for p in items if p.sellable_separately and (p.code or "").strip())
    composition = len(items) - sellable
    return {
        "sellable_parts": sellable,
        "composition_only": composition,
        "source_doc_types": list(schema.source_doc_types),
        "low_confidence_fields": list(schema.low_confidence_fields),
        "document_conflicts": len(schema.document_conflicts),
    }
