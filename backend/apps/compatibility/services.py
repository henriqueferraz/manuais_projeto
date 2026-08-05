"""Consultas de compatibilidade (ORM)."""

from __future__ import annotations

from django.db.models import QuerySet

from apps.compatibility.models import Compatibility
from apps.products.models import Product


def parts_for_equipment(*, brand: str = "", model: str = "") -> QuerySet[Product]:
    """Lista peças publicadas compatíveis com marca/modelo informado."""
    qs = Compatibility.objects.select_related("part_product", "part_product__stock")
    if brand:
        qs = qs.filter(equipment_brand__icontains=brand.strip())
    if model:
        qs = qs.filter(equipment_model__icontains=model.strip())

    product_ids = qs.values_list("part_product_id", flat=True).distinct()
    return (
        Product.objects.filter(
            id__in=product_ids,
            status=Product.Status.PUBLISHED,
            product_kind=Product.Kind.SPARE_PART,
        )
        .select_related("stock", "category")
        .prefetch_related("translations", "images")
    )


def compat_labels_for_product(product: Product) -> list[str]:
    rows = Compatibility.objects.filter(part_product=product).order_by(
        "equipment_brand", "equipment_model"
    )[:12]
    return [f"{r.equipment_brand} {r.equipment_model}".strip() for r in rows]
