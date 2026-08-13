"""Assistente de IA no formulário de produto (upload PDF → preview HITL)."""

from __future__ import annotations

import re
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
from apps.manuals.services.structure import (
    ensure_sales_description,
    prepare_extracted_product,
    promote_canonical_fields,
)
from apps.products.libraries.field_style import apply_field_style
from apps.products.models import Product


def _unique_slug(model, text: str, *, max_len: int = 140) -> str:
    """Gera slug único para Brand/Category/EquipmentModel."""
    base = slugify(text)[:max_len] or "item"
    slug = base
    n = 2
    while model.objects.filter(slug=slug).exists():
        suffix = f"-{n}"
        slug = f"{base[: max_len - len(suffix)]}{suffix}"
        n += 1
    return slug


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
        schema = prepare_extracted_product(schema, log.raw_text_preview or "")
        product_data = schema.model_dump(mode="json")
    except Exception:  # noqa: BLE001
        schema = None
        product_data = raw

    summary = extraction_review_summary(product_data)
    parts_review = parts_for_review(schema or product_data)
    source = schema or product_data
    form_suggestions = build_form_suggestions(source)
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
        "parts_for_review": parts_review,
        "proposal_sections": build_proposal_sections(source),
        "model_options": collect_model_options(
            source,
            brand_name=str(form_suggestions.get("brand_name") or ""),
        ),
        "form_suggestions": form_suggestions,
        "awaiting_approval": True,
        "message": (
            "A IA leu o PDF e propôs os dados abaixo. "
            "Nada foi aplicado ao formulário nem ao catálogo — aguarde sua aprovação. "
            "Se houver vários modelos, escolha qual cadastrar agora. "
            "Ao salvar, o manual PDF fica vinculado ao produto (download na página) "
            "e as peças marcadas são cadastradas em rascunho."
        ),
    }


def parts_for_review(data: ExtractedProduct | dict[str, Any]) -> list[dict[str, Any]]:
    """Lista peças/acessórios para o painel HITL (checkbox antes do save)."""
    from apps.manuals.schemas import RelatedPartHint

    rows: list[dict[str, Any]] = []

    def _append(raw_items: list, *, kind: str) -> None:
        for idx, raw in enumerate(raw_items):
            try:
                part = (
                    raw if isinstance(raw, RelatedPartHint) else RelatedPartHint.model_validate(raw)
                )
            except Exception:  # noqa: BLE001  # nosec B112
                continue
            code = (part.code or "").strip()
            sellable = bool(part.sellable_separately and code)
            rows.append(
                {
                    "key": code or f"{kind}-{idx}",
                    "code": code,
                    "name": (part.name or part.description or "Peça sem nome")[:200],
                    "sku_suggestion": (part.sku_suggestion or "")[:64],
                    "ref_number": part.ref_number or "",
                    "qty_per_unit": part.qty_per_unit,
                    "sellable_separately": sellable,
                    "selected": sellable,
                    "kind": kind,
                    "category": (part.category or "")[:120],
                }
            )

    if isinstance(data, ExtractedProduct):
        _append(list(data.spare_parts), kind="spare_part")
        _append(list(data.accessories), kind="accessory")
    else:
        _append(list(data.get("spare_parts") or []), kind="spare_part")
        _append(list(data.get("accessories") or []), kind="accessory")
    return rows


def build_form_suggestions(data: ExtractedProduct | dict[str, Any]) -> dict[str, Any]:
    """Mapeia extração → campos do InternalProductForm (sem gravar)."""
    if isinstance(data, ExtractedProduct):
        p = data
    else:
        try:
            p = ExtractedProduct.model_validate(data)
        except Exception:  # noqa: BLE001
            return {}

    p = ensure_sales_description(p)
    dump = p.model_dump(mode="json")

    brand_id = None
    brand_name = (p.brand or p.manufacturer or "").strip()
    if brand_name and brand_name.casefold() not in {"desconhecida", "unknown", "n/a"}:
        brand = Brand.objects.filter(name__iexact=brand_name).first()
        if brand is None:
            brand = Brand.objects.filter(name__icontains=brand_name).first()
        if brand is None:
            brand = Brand.objects.create(
                name=brand_name[:120],
                slug=_unique_slug(Brand, brand_name, max_len=140),
            )
        brand_id = brand.pk
        brand_name = brand.name

    category_id = None
    cat_hint = (p.category or p.category_hint or "").strip()
    if cat_hint:
        from apps.products.libraries.field_style import initial_cap

        cat_hint = initial_cap(cat_hint)
        category = Category.objects.filter(name__iexact=cat_hint).first()
        if category is None:
            slug = slugify(cat_hint)[:140]
            category = Category.objects.filter(slug=slug).first()
        if category is None:
            category = Category.objects.filter(name__icontains=cat_hint).first()
        if category is None:
            category = Category.objects.create(
                name=cat_hint[:120],
                slug=_unique_slug(Category, cat_hint, max_len=140),
            )
        elif category.name != cat_hint and category.name.casefold() == cat_hint.casefold():
            category.name = cat_hint
            category.save(update_fields=["name", "updated_at"])
        category_id = category.pk
        cat_hint = category.name

    equipment_model_id = None
    model_code = (p.model_code or "").split("/")[0].strip()
    if model_code and model_code.casefold() not in {"sem-modelo", "unknown", "n/a"}:
        em = EquipmentModel.objects.filter(code__iexact=model_code).first()
        if em is None and brand_name:
            em = EquipmentModel.objects.filter(
                brand__iexact=brand_name, code__icontains=model_code
            ).first()
        if em is None:
            em = EquipmentModel.objects.create(
                code=model_code[:120],
                brand=(brand_name or "")[:120],
                name=(p.name or model_code)[:255],
                slug=_unique_slug(
                    EquipmentModel,
                    f"{brand_name}-{model_code}" if brand_name else model_code,
                    max_len=160,
                ),
            )
        elif brand_name and not em.brand:
            em.brand = brand_name[:120]
            em.save(update_fields=["brand", "updated_at"])
        equipment_model_id = em.pk
        model_code = em.code

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
        "model_variants": list(dump.get("model_variants") or []),
        "confidence": float(dump.get("confidence") or 0.5),
        "low_confidence_fields": list(dump.get("low_confidence_fields") or []),
    }
    return apply_field_style(suggestions)


def _format_list_value(value: Any, *, limit: int = 8) -> str:
    items = [str(v).strip() for v in (value or []) if str(v).strip()]
    if not items:
        return ""
    if len(items) > limit:
        return "; ".join(items[:limit]) + f"; …(+{len(items) - limit})"
    return "; ".join(items)


def _specs_extra_lines(dump: dict[str, Any]) -> str:
    """Linhas chave=valor para o textarea specs_extra (campos não mapeados).

    Chaves técnicas canônicas (snake_case); rótulos pt-BR ficam só na exibição.
    """
    from apps.products.specs_display import (
        _expand_warranty,
        canonicalize_spec_key,
    )

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
        "low_confidence_fields",
        "document_conflicts",
        "troubleshooting",
        "assembly_summary",
        "warranty",
        "safety_warnings",
        "key_usage_steps",
        "installation_requirements",
        "certifications",
        "model_variants",
        "notes",
        "source_doc_types",
    }
    mapped_spec_keys = {
        "blade_count",
        "diameter_cm",
        "material",
        "color",
        "rpm",
        "mounting",
        "bearing_type",
        "remote_included",
        # potencia/power nunca vão para specs_extra — campo canônico é power_w
        "potencia",
        "potência",
        "power",
        "power_w",
        "potencia_w",
        "potência_w",
    }
    warranty_flat = {
        "warranty_legal_days",
        "warranty_additional_days",
        "warranty_total_days",
        "legal_days",
        "additional_days",
        "total_days",
    }
    lines: list[str] = []
    seen_keys: set[str] = set()

    def add(key: str, value: Any) -> None:
        if value in (None, "", [], {}):
            return
        canon = canonicalize_spec_key(key)
        if not canon or canon in seen_keys:
            return
        if isinstance(value, (dict, list)):
            return
        seen_keys.add(canon)
        lines.append(f"{canon}={value}")

    specs = dump.get("specs") or {}
    if isinstance(specs, dict):
        if "warranty" in specs or any(canonicalize_spec_key(str(k)) == "warranty" for k in specs):
            raw_w = specs.get("warranty")
            if raw_w is None:
                for k, v in specs.items():
                    if canonicalize_spec_key(str(k)) == "warranty":
                        raw_w = v
                        break
            for wcanon, wv in _expand_warranty(raw_w):
                add(wcanon, wv)
        for key, value in specs.items():
            canon = canonicalize_spec_key(str(key))
            if (
                not canon
                or canon in mapped_spec_keys
                or canon == "warranty"
                or canon in warranty_flat
                or value in (None, "", [], {})
            ):
                continue
            if isinstance(value, list):
                formatted = _format_list_value(value)
                if formatted:
                    add(canon, formatted)
                continue
            if isinstance(value, dict):
                continue
            add(canon, value)

    for key in (
        "capacity",
        "ean",
        "barcode",
        "ncm_classification",
        "frequency_hz",
        "consumption_kwh",
        "packaging_qty",
    ):
        add(key, dump.get(key))

    variants = dump.get("model_variants") or []
    if variants:
        add(
            "model_variants",
            ", ".join(str(v).strip() for v in variants if str(v).strip()),
        )

    warranty = dump.get("warranty") or {}
    if isinstance(warranty, dict):
        for wcanon, wv in _expand_warranty(warranty):
            add(wcanon, wv)

    for list_key in (
        "safety_warnings",
        "key_usage_steps",
        "installation_requirements",
        "certifications",
        "source_doc_types",
    ):
        formatted = _format_list_value(dump.get(list_key))
        if formatted:
            add(list_key, formatted)

    notes = dump.get("notes")
    if notes:
        add("notes", str(notes)[:500])

    for key, value in dump.items():
        canon = canonicalize_spec_key(str(key))
        if canon in skip or canon in seen_keys or value in (None, "", [], {}):
            continue
        if isinstance(value, (dict, list)):
            continue
        add(canon, value)

    return "\n".join(lines[:60])


def _clean_str_list(value: Any, *, limit: int = 10) -> list[str]:
    return [str(x).strip() for x in (value or []) if str(x).strip()][:limit]


def build_proposal_sections(data: ExtractedProduct | dict[str, Any]) -> dict[str, Any]:
    """Blocos resumidos para a UI HITL (além do JSON completo)."""
    from apps.products.specs_display import (
        _expand_warranty,
        canonicalize_spec_key,
        format_spec_value,
        label_for_spec_key,
    )

    if isinstance(data, ExtractedProduct):
        data = promote_canonical_fields(data)
        dump = data.model_dump(mode="json")
    else:
        try:
            data = promote_canonical_fields(ExtractedProduct.model_validate(data))
            dump = data.model_dump(mode="json")
        except Exception:  # noqa: BLE001
            dump = dict(data or {})

    skip_char_keys = {
        "warranty",
        "safety_warnings",
        "key_usage_steps",
        "installation_requirements",
        "certifications",
        "source_doc_types",
        "model_variants",
        "warranty_legal_days",
        "warranty_additional_days",
        "warranty_total_days",
        "legal_days",
        "additional_days",
        "total_days",
        # potencia/power → campo canônico power_w (não listar em Características)
        "potencia",
        "potência",
        "power",
        "power_w",
        "potencia_w",
        "potência_w",
    }
    specs = dump.get("specs") or {}
    characteristics: list[str] = []
    if isinstance(specs, dict):
        for k, v in specs.items():
            canon = canonicalize_spec_key(str(k))
            if (
                not canon
                or canon in skip_char_keys
                or v in (None, "", [], {})
                or isinstance(v, dict)
            ):
                continue
            label = label_for_spec_key(canon)
            characteristics.append(f"{label}: {format_spec_value(v)}")
            if len(characteristics) >= 12:
                break

    warranty_lines: list[str] = []
    warranty = dump.get("warranty") or {}
    if isinstance(warranty, dict):
        for wcanon, wv in _expand_warranty(warranty):
            warranty_lines.append(f"{label_for_spec_key(wcanon)}: {format_spec_value(wv)}")
    elif isinstance(specs, dict):
        raw_w = specs.get("warranty")
        if raw_w is None:
            for k, v in specs.items():
                if canonicalize_spec_key(str(k)) == "warranty":
                    raw_w = v
                    break
        for wcanon, wv in _expand_warranty(raw_w):
            warranty_lines.append(f"{label_for_spec_key(wcanon)}: {format_spec_value(wv)}")

    def _list_from_dump_or_specs(key: str, *, limit: int) -> list[str]:
        items = _clean_str_list(dump.get(key), limit=limit)
        if items:
            return items
        if isinstance(specs, dict):
            for sk, sv in specs.items():
                if canonicalize_spec_key(str(sk)) == key:
                    if isinstance(sv, list):
                        return _clean_str_list(sv, limit=limit)
                    if isinstance(sv, str) and sv.strip():
                        return _clean_str_list(
                            [p.strip() for p in sv.split(";") if p.strip()],
                            limit=limit,
                        )
        return []

    variants = _clean_str_list(dump.get("model_variants"), limit=40)
    model_code = str(dump.get("model_code") or "").strip()
    if model_code and "/" in model_code:
        for part in model_code.split("/"):
            code = part.strip()
            if code and code not in variants:
                variants.append(code)

    components: list[str] = []
    raw_components = dump.get("components") or []
    if isinstance(raw_components, list):
        for item in raw_components[:20]:
            if isinstance(item, dict):
                number = str(item.get("number") or "").strip()
                name = str(item.get("name") or "").strip()
            else:
                number = str(getattr(item, "number", "") or "").strip()
                name = str(getattr(item, "name", "") or "").strip()
            if not name and not number:
                continue
            if number and name:
                components.append(f"{number} — {name}")
            else:
                components.append(name or number)

    return {
        "characteristics": characteristics,
        "components": components,
        "safety_warnings": _list_from_dump_or_specs("safety_warnings", limit=10),
        "key_usage_steps": _list_from_dump_or_specs("key_usage_steps", limit=10),
        "installation_requirements": _list_from_dump_or_specs("installation_requirements", limit=8),
        "warranty": warranty_lines,
        "model_variants": variants,
        "certifications": _list_from_dump_or_specs("certifications", limit=8),
    }


def collect_model_options(
    data: ExtractedProduct | dict[str, Any],
    *,
    brand_name: str = "",
) -> list[dict[str, Any]]:
    """Modelos candidatos (principal + variantes) com SKU e equipment_model para o HITL."""
    sections = build_proposal_sections(data)
    codes: list[str] = []
    if isinstance(data, ExtractedProduct):
        primary = (data.model_code or "").strip()
        brand = brand_name or (data.brand or data.manufacturer or "")
        product_name = data.name or ""
    else:
        primary = str((data or {}).get("model_code") or "").strip()
        raw_brand = (data or {}).get("brand") or (data or {}).get("manufacturer") or ""
        brand = brand_name or str(raw_brand)
        product_name = str((data or {}).get("name") or "")

    unknown_models = {"sem-modelo", "unknown", "n/a"}
    if primary and "/" not in primary and primary.casefold() not in unknown_models:
        codes.append(primary)
    elif primary and "/" in primary:
        for part in primary.split("/"):
            code = part.strip()
            if code and code not in codes:
                codes.append(code)
    for variant in sections.get("model_variants") or []:
        if variant and variant not in codes:
            codes.append(variant)

    options: list[dict[str, Any]] = []
    for code in codes:
        em = EquipmentModel.objects.filter(code__iexact=code).first()
        if em is None and brand:
            em = EquipmentModel.objects.filter(brand__iexact=brand, code__icontains=code).first()
        if em is None:
            em = EquipmentModel.objects.create(
                code=code[:120],
                brand=(brand or "")[:120],
                name=(product_name or code)[:255],
                slug=_unique_slug(
                    EquipmentModel,
                    f"{brand}-{code}" if brand else code,
                    max_len=160,
                ),
            )
        elif brand and not em.brand:
            em.brand = brand[:120]
            em.save(update_fields=["brand", "updated_at"])
        brand_slug = re.sub(r"[^A-Z0-9]", "", (brand or "XX").upper())[:8] or "XX"
        sku = f"{brand_slug}-{code}".upper().replace(" ", "-")[:64]
        options.append(
            {
                "code": code,
                "equipment_model_id": em.pk,
                "sku": sku,
                "label": f"{brand} {code}".strip() if brand else code,
            }
        )
    return options


def discard_product_form_extraction(
    *,
    extraction_id: int,
    user: AbstractBaseUser,
    notes: str = "Descartado no formulário de produto",
) -> ExtractionLog:
    """Rejeita extração do formulário de produto sem aplicar dados ao catálogo."""
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
    selected_part_codes: set[str] | None = None,
) -> dict[str, Any] | None:
    """
    Após o humano aprovar a aplicação no formulário e salvar o produto,
    vincula o Manual e materializa peças selecionadas.
    O PDF do manual NÃO vira foto de vitrine (R21) — fica disponível para download.
    """
    from django.utils import timezone

    from apps.accounts.models import SensitiveActionLog
    from apps.manuals.services.pipeline import (
        _materialize_related_parts,
        _merge_product_specs,
        enqueue_manual_rag_index,
    )
    from apps.manuals.services.structure import dump_product_json, prepare_extracted_product

    try:
        log = ExtractionLog.objects.select_related("manual").get(pk=extraction_id)
    except ExtractionLog.DoesNotExist:
        return None

    if log.status not in {
        ExtractionLog.Status.AWAITING_REVIEW,
        ExtractionLog.Status.APPROVED,
        ExtractionLog.Status.REJECTED,
    }:
        return {"log": log, "parts": [], "manual_linked": False, "cover_attached": False}

    data = log.corrected_json or log.raw_json or {}
    try:
        schema = ExtractedProduct.model_validate(data)
        # Reaplica normalização no save (extrações antigas / JSON sem código sintético).
        schema = prepare_extracted_product(schema, log.raw_text_preview or "")
    except Exception:  # noqa: BLE001
        schema = None

    materialized: dict[str, Any] = {
        "created": 0,
        "reused": 0,
        "compatibilities": 0,
        "part_products": [],
    }

    # Merge specs órfãos sem sobrescrever o que o usuário editou no form
    if schema is not None:
        merged = dict(product.specs or {})
        for key, value in _merge_product_specs(schema).items():
            merged.setdefault(key, value)
        product.specs = merged
        product.manual = log.manual
        product.extraction_confidence = schema.confidence
        product.save(update_fields=["specs", "manual", "extraction_confidence", "updated_at"])
        # selected_part_codes=None → todas vendáveis; set vazio → nenhuma peça
        codes = selected_part_codes if selected_part_codes is not None else None
        if codes is None:
            # default: todas as vendáveis com código (após normalização)
            codes = {
                (p.code or "").strip()
                for p in list(schema.spare_parts) + list(schema.accessories)
                if p.sellable_separately and (p.code or "").strip()
            }
        materialized = _materialize_related_parts(product, schema, selected_codes=codes)
        log.corrected_json = dump_product_json(schema)
    else:
        product.manual = log.manual
        product.save(update_fields=["manual", "updated_at"])

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

    # Mesmo caminho do approve HITL da fila de manuais: indexar PDF para o chat RAG.
    enqueue_manual_rag_index(log.manual_id)

    SensitiveActionLog.objects.create(
        action=SensitiveActionLog.Action.OTHER,
        actor=user if getattr(user, "is_authenticated", False) else None,
        object_repr=f"Vinculou extração #{log.pk} ao produto {product.sku}",
        details={
            "extraction_id": log.pk,
            "product_id": product.pk,
            "parts_created": materialized.get("created", 0),
            "parts_reused": materialized.get("reused", 0),
            "manual_linked": True,
            "cover_attached": False,
        },
    )
    return {
        "log": log,
        "parts": list(materialized.get("part_products") or []),
        "manual_linked": True,
        "cover_attached": False,
        "parts_created": materialized.get("created", 0),
        "parts_reused": materialized.get("reused", 0),
    }


def attach_manual_cover_as_product_image(product: Product, manual) -> Any | None:
    """
    Legado: não usar no fluxo de cadastro.

    A capa do PDF não conta como foto de vitrine (R21). O manual fica
    vinculado em ``product.manual`` para download na página do produto.
    """
    return None


def related_spare_parts_for_product(product: Product) -> list[Product]:
    """Peças vinculadas ao produto principal (inclui draft — uso no dashboard)."""
    from apps.compatibility.models import Compatibility

    if product.product_kind == Product.Kind.SPARE_PART:
        return []

    ids: set[int] = set()
    if product.brand and (product.model_code or product.sku):
        model_hint = product.model_code or product.sku
        ids.update(
            Compatibility.objects.filter(
                equipment_brand__iexact=product.brand,
                equipment_model__icontains=model_hint,
            ).values_list("part_product_id", flat=True)
        )
    ids.update(
        Product.objects.filter(
            product_kind=Product.Kind.SPARE_PART,
            specs__parent_sku=product.sku,
        ).values_list("id", flat=True)
    )
    if not ids:
        return []
    return list(
        Product.objects.filter(id__in=ids, product_kind=Product.Kind.SPARE_PART)
        .select_related("stock", "category", "equipment_model", "brand_ref")
        .prefetch_related("translations")
        .order_by("sku")
    )


def related_part_modal_payload(part: Product) -> dict[str, Any]:
    """Dados leves para o modal de peça vinculada (mesma tela)."""
    specs = part.specs or {}
    return {
        "id": part.pk,
        "sku": part.sku,
        "name": part.name_pt or part.sku,
        "description": (part.description_pt or "")[:2000],
        "brand": part.brand or "",
        "model_code": part.model_code or "",
        "equipment_model": (
            str(part.equipment_model) if part.equipment_model_id else part.model_code or ""
        ),
        "category": (part.category.name if part.category_id else "Peça de reposição"),
        "status": part.get_status_display(),
        "price": str(part.price),
        "part_code": str(specs.get("part_code") or ""),
        "ref_number": str(specs.get("ref_number") or ""),
        "qty_per_unit": specs.get("qty_per_unit"),
        "parent_sku": str(specs.get("parent_sku") or ""),
    }
