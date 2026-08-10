"""Assistente de IA no formulário de produto (upload PDF → preview HITL)."""

from __future__ import annotations

from typing import Any

from django.contrib.auth.models import AbstractBaseUser
from django.utils.text import slugify

from apps.catalog.models import Brand, Category, EquipmentModel
from apps.manuals.models import ExtractionLog
from apps.manuals.schemas import ExtractedProduct
from apps.manuals.services.pipeline import (
    create_manual_from_upload,
    extraction_review_summary,
    reject_extraction,
    run_extraction,
)
from apps.products.models import Product


def extract_manual_for_product_form(
    *,
    content: bytes,
    filename: str,
    user: AbstractBaseUser,
    manufacturer: str = "",
) -> dict[str, Any]:
    """
    Upload + antivírus (via validate_manual_upload) + extração.

    NÃO cria Product nem aplica dados ao formulário — só deixa o ExtractionLog
    em awaiting_review para o humano aprovar.
    """
    manual, log = create_manual_from_upload(
        content=content,
        filename=filename,
        user=user,
        manufacturer=manufacturer,
        enqueue=False,
    )
    run_extraction(log.pk)
    log.refresh_from_db()

    if log.status == ExtractionLog.Status.FAILED:
        return {
            "ok": False,
            "error": log.error_message or "Falha na extração do PDF.",
            "extraction_id": log.pk,
            "manual_id": manual.pk,
            "scan_status": manual.scan_status,
        }

    if log.status != ExtractionLog.Status.AWAITING_REVIEW:
        return {
            "ok": False,
            "error": f"Status inesperado após extração: {log.status}",
            "extraction_id": log.pk,
            "manual_id": manual.pk,
            "scan_status": manual.scan_status,
        }

    raw = log.raw_json or {}
    try:
        schema = ExtractedProduct.model_validate(raw)
        product_data = schema.model_dump(mode="json")
    except Exception:  # noqa: BLE001
        schema = None
        product_data = raw

    summary = extraction_review_summary(product_data)
    return {
        "ok": True,
        "extraction_id": log.pk,
        "manual_id": manual.pk,
        "filename": manual.original_filename,
        "scan_status": manual.scan_status,
        "confidence": log.confidence,
        "prompt_version": log.prompt_version,
        "model_name": log.model_name,
        "summary": summary,
        "extracted": product_data,
        "form_suggestions": build_form_suggestions(schema or product_data),
        "awaiting_approval": True,
        "message": (
            "A IA leu o PDF e propôs os dados abaixo. "
            "Nada foi aplicado ao formulário nem ao catálogo — aguarde sua aprovação."
        ),
    }


def build_form_suggestions(data: ExtractedProduct | dict[str, Any]) -> dict[str, Any]:
    """Mapeia extração → campos do InternalProductForm (sem gravar)."""
    if isinstance(data, ExtractedProduct):
        p = data
        dump = data.model_dump(mode="json")
    else:
        try:
            p = ExtractedProduct.model_validate(data)
            dump = p.model_dump(mode="json")
        except Exception:  # noqa: BLE001
            return {}

    brand_id = None
    brand_name = (p.brand or p.manufacturer or "").strip()
    if brand_name:
        brand = Brand.objects.filter(name__iexact=brand_name).first()
        if brand is None:
            brand = Brand.objects.filter(name__icontains=brand_name).first()
        if brand:
            brand_id = brand.pk

    category_id = None
    cat_hint = (p.category or p.category_hint or "").strip()
    if cat_hint:
        category = Category.objects.filter(name__iexact=cat_hint).first()
        if category is None:
            slug = slugify(cat_hint)[:140]
            category = Category.objects.filter(slug=slug).first()
        if category is None:
            category = Category.objects.filter(name__icontains=cat_hint).first()
        if category:
            category_id = category.pk

    equipment_model_id = None
    model_code = (p.model_code or "").split("/")[0].strip()
    if model_code:
        em = EquipmentModel.objects.filter(code__iexact=model_code).first()
        if em is None and brand_name:
            em = EquipmentModel.objects.filter(
                brand__iexact=brand_name, code__icontains=model_code
            ).first()
        if em:
            equipment_model_id = em.pk

    specs = dict(p.specs or {})
    dims = p.dimensions_mm or p.dimensions or {}

    def _dim(*keys: str):
        for key in keys:
            if dims.get(key) not in (None, ""):
                return dims.get(key)
            # também em cm se vier mm
            if key.endswith("_mm") and dims.get(key):
                return dims.get(key)
        return ""

    suggestions: dict[str, Any] = {
        "sku": (p.sku_suggestion or "")[:64],
        "brand_ref": brand_id,
        "brand_name": brand_name,
        "equipment_model": equipment_model_id,
        "model_code": model_code,
        "name": p.name or "",
        "description": p.description or "",
        "voltage": p.voltage or "",
        "product_kind": p.product_kind or Product.Kind.FINISHED_GOOD,
        "status": Product.Status.DRAFT,
        "category": category_id,
        "category_name": cat_hint,
        "power_w": p.power_w if p.power_w is not None else "",
        "weight_kg": p.weight_kg if p.weight_kg is not None else "",
        "dim_height_cm": _dim("altura_cm", "height_cm", "altura", "height", "altura_mm"),
        "dim_width_cm": _dim("largura_cm", "width_cm", "largura", "width", "largura_mm"),
        "dim_depth_cm": _dim(
            "profundidade_cm", "depth_cm", "profundidade", "depth", "profundidade_mm"
        ),
        "diameter_cm": specs.get("diameter_cm", ""),
        "blade_count": specs.get("blade_count", ""),
        "material": specs.get("material", ""),
        "color": specs.get("color", ""),
        "rpm": specs.get("rpm", ""),
        "mounting": specs.get("mounting", ""),
        "bearing_type": specs.get("bearing_type", ""),
        "remote_included": bool(specs.get("remote_included")),
        "specs_extra": _specs_extra_lines(dump),
    }
    return suggestions


def _specs_extra_lines(dump: dict[str, Any]) -> str:
    """Linhas chave=valor para o textarea specs_extra (campos não mapeados)."""
    skip = {
        "brand",
        "model_code",
        "name",
        "description",
        "sku_suggestion",
        "product_kind",
        "category",
        "category_hint",
        "voltage",
        "power_w",
        "weight_kg",
        "dimensions",
        "dimensions_mm",
        "specs",
        "spare_parts",
        "accessories",
        "components",
        "confidence",
        "manufacturer",
    }
    lines: list[str] = []
    specs = dump.get("specs") or {}
    mapped_spec_keys = {
        "blade_count",
        "diameter_cm",
        "material",
        "color",
        "rpm",
        "mounting",
        "bearing_type",
        "remote_included",
    }
    for key, value in specs.items():
        if key in mapped_spec_keys or value in (None, "", [], {}):
            continue
        lines.append(f"{key}={value}")
    for key in (
        "capacity",
        "ean",
        "ncm_classification",
        "frequency_hz",
        "consumption_kwh",
        "packaging_qty",
    ):
        value = dump.get(key)
        if value not in (None, "", [], {}):
            lines.append(f"{key}={value}")
    for key, value in dump.items():
        if key in skip or value in (None, "", [], {}):
            continue
        if key in {
            "capacity",
            "ean",
            "barcode",
            "ncm_classification",
            "frequency_hz",
            "consumption_kwh",
            "packaging_qty",
            "source_doc_types",
            "model_variants",
            "notes",
            "certifications",
        }:
            if isinstance(value, list):
                lines.append(f"{key}={', '.join(str(v) for v in value)}")
            elif isinstance(value, dict):
                continue
            else:
                if f"{key}=" not in "\n".join(lines):
                    lines.append(f"{key}={value}")
    return "\n".join(lines[:40])


def discard_product_form_extraction(
    *,
    extraction_id: int,
    user: AbstractBaseUser,
    notes: str = "Descartado no formulário de produto",
) -> ExtractionLog:
    log = ExtractionLog.objects.select_related("manual").get(pk=extraction_id)
    if log.status not in {
        ExtractionLog.Status.AWAITING_REVIEW,
        ExtractionLog.Status.APPROVED,
    }:
        return log
    return reject_extraction(
        log,
        reviewer=user,
        notes=notes,
        skip_graph_resume=True,
    )


def link_approved_extraction_to_product(
    *,
    extraction_id: int,
    product: Product,
    user: AbstractBaseUser,
) -> ExtractionLog | None:
    """
    Após o humano aprovar a aplicação no formulário e salvar o produto,
    vincula o Manual e marca a extração como aprovada (sem recriar o Product).
    """
    from django.utils import timezone

    from apps.accounts.models import SensitiveActionLog
    from apps.manuals.services.pipeline import _materialize_related_parts, _merge_product_specs
    from apps.manuals.services.structure import dump_product_json

    try:
        log = ExtractionLog.objects.select_related("manual").get(pk=extraction_id)
    except ExtractionLog.DoesNotExist:
        return None

    if log.status not in {
        ExtractionLog.Status.AWAITING_REVIEW,
        ExtractionLog.Status.APPROVED,
        ExtractionLog.Status.REJECTED,
    }:
        return log

    data = log.corrected_json or log.raw_json or {}
    try:
        schema = ExtractedProduct.model_validate(data)
    except Exception:  # noqa: BLE001
        schema = None

    # Merge specs órfãos sem sobrescrever o que o usuário editou no form
    if schema is not None:
        merged = dict(product.specs or {})
        for key, value in _merge_product_specs(schema).items():
            merged.setdefault(key, value)
        product.specs = merged
        product.manual = log.manual
        product.extraction_confidence = schema.confidence
        product.save(update_fields=["specs", "manual", "extraction_confidence", "updated_at"])
        _materialize_related_parts(product, schema)
        log.corrected_json = dump_product_json(schema)

    log.status = ExtractionLog.Status.APPROVED
    log.reviewed_by = user if getattr(user, "is_authenticated", False) else None
    log.reviewed_at = timezone.now()
    log.draft_product = product
    log.langgraph_interrupted = False
    if not log.review_notes:
        log.review_notes = "Aprovado via formulário de produto (dashboard)."
    log.save()

    log.manual.linked_product = product
    log.manual.save(update_fields=["linked_product", "updated_at"])

    SensitiveActionLog.objects.create(
        action=SensitiveActionLog.Action.OTHER,
        actor=user if getattr(user, "is_authenticated", False) else None,
        object_repr=f"Vinculou extração #{log.pk} ao produto {product.sku}",
        details={"extraction_id": log.pk, "product_id": product.pk},
    )
    return log
