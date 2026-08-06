"""Recomendação de SKUs a partir de sintoma + chunks (F6)."""

from __future__ import annotations

import re

from django.db.models import Q

from apps.compatibility.services import parts_for_equipment
from apps.products.models import Product

_SKU_RE = re.compile(r"\b([A-Z]{2,}[A-Z0-9\-]{2,})\b")
_CAPACITOR = re.compile(r"capacitor", re.I)
_PA = re.compile(r"\bp[aá]s?\b", re.I)


def recommend_skus_for_symptom(
    symptom: str,
    *,
    product_id: int | None = None,
    chunk_texts: list[str] | None = None,
    limit: int = 4,
) -> list[str]:
    """Extrai SKUs dos trechos e cruza com catálogo / compatibilidade."""
    texts = list(chunk_texts or [])
    texts.append(symptom)
    blob = "\n".join(texts)

    candidates: list[str] = []
    for match in _SKU_RE.findall(blob.upper()):
        if match not in candidates and not match.startswith("HTTP"):
            candidates.append(match)

    published = {
        p.sku.upper(): p.sku
        for p in Product.objects.filter(
            status=Product.Status.PUBLISHED,
            sku__in=candidates[:20],
        ).only("sku")
    }
    skus = [published[c] for c in candidates if c in published]

    equipment = None
    if product_id:
        equipment = Product.objects.filter(pk=product_id).first()

    if equipment and len(skus) < limit:
        compat = parts_for_equipment(brand=equipment.brand, model=equipment.model_code)
        if _CAPACITOR.search(symptom) or _CAPACITOR.search(blob):
            compat = compat.filter(
                Q(sku__icontains="CAP")
                | Q(translations__name__icontains="capacitor")
                | Q(model_code__icontains="CAP")
            ).distinct()
        elif _PA.search(symptom) or _PA.search(blob):
            compat = compat.filter(
                Q(sku__icontains="PAL")
                | Q(translations__name__icontains="pá")
                | Q(translations__name__icontains="pa ")
            ).distinct()
        for part in compat[:limit]:
            if part.sku not in skus:
                skus.append(part.sku)

    if len(skus) < limit:
        # Fallback: spares published matching keyword in SKU/name
        q = Q()
        if _CAPACITOR.search(blob):
            q |= Q(sku__icontains="CAP") | Q(translations__name__icontains="capacitor")
        if _PA.search(blob):
            q |= Q(sku__icontains="PAL") | Q(translations__name__icontains="pá")
        if q:
            extras = (
                Product.objects.filter(
                    status=Product.Status.PUBLISHED, product_kind=Product.Kind.SPARE_PART
                )
                .filter(q)
                .distinct()[:limit]
            )
            for p in extras:
                if p.sku not in skus:
                    skus.append(p.sku)

    return skus[:limit]
