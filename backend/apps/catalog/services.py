"""Consulta e cache do catálogo."""

from __future__ import annotations

from django.conf import settings
from django.core.cache import cache
from django.db import connection
from django.db.models import Prefetch, Q, QuerySet

from apps.products.models import Product, ProductTranslation

CACHE_TTL = int(getattr(settings, "CATALOG_CACHE_TTL", 60))


def published_products() -> QuerySet[Product]:
    return (
        Product.objects.filter(status=Product.Status.PUBLISHED)
        .select_related("category", "stock")
        .prefetch_related(
            Prefetch(
                "translations",
                queryset=ProductTranslation.objects.filter(locale="pt-BR"),
            ),
            "images",
        )
    )


def filter_catalog(
    *,
    q: str = "",
    category: str = "",
    voltage: str = "",
    model: str = "",
    brand: str = "",
    compat_model: str = "",
) -> QuerySet[Product]:
    qs = published_products()

    if category:
        qs = qs.filter(Q(category__slug=category) | Q(category__name__iexact=category))
    if voltage:
        qs = qs.filter(voltage__iexact=voltage)
    if model:
        qs = qs.filter(model_code__icontains=model)
    if brand:
        qs = qs.filter(brand__icontains=brand)
    if compat_model:
        qs = qs.filter(
            Q(model_code__icontains=compat_model)
            | Q(
                compatibilities__equipment_model__icontains=compat_model,
                product_kind=Product.Kind.SPARE_PART,
            )
        ).distinct()

    q = (q or "").strip()
    if q:
        qs = _full_text_or_icontains(qs, q)

    return qs.order_by("brand", "model_code", "sku")


def _full_text_or_icontains(qs: QuerySet[Product], q: str) -> QuerySet[Product]:
    if connection.vendor == "postgresql":
        from django.contrib.postgres.search import SearchQuery, SearchRank, SearchVector

        vector = (
            SearchVector("sku", weight="A")
            + SearchVector("brand", weight="A")
            + SearchVector("model_code", weight="A")
            + SearchVector("translations__name", weight="B")
            + SearchVector("translations__description", weight="C")
        )
        query = SearchQuery(q, config="portuguese")
        return (
            qs.annotate(search=vector, rank=SearchRank(vector, query))
            .filter(search=query)
            .order_by("-rank", "brand")
        )

    return qs.filter(
        Q(sku__icontains=q)
        | Q(brand__icontains=q)
        | Q(model_code__icontains=q)
        | Q(translations__name__icontains=q)
        | Q(translations__description__icontains=q)
    ).distinct()


def cached_filter_count(cache_key: str, qs: QuerySet[Product]) -> int:
    """Cacheia contagem de listagens quentes (Redis/locmem)."""
    hit = cache.get(cache_key)
    if hit is not None:
        return int(hit)
    count = qs.count()
    cache.set(cache_key, count, CACHE_TTL)
    return count


def autocomplete(q: str, *, limit: int = 8) -> list[dict]:
    q = (q or "").strip()
    if len(q) < 2:
        return []
    key = f"catalog:ac:{q.lower()[:40]}"
    cached = cache.get(key)
    if cached is not None:
        return cached

    qs = filter_catalog(q=q)[:limit]
    results = []
    for p in qs:
        img = p.primary_image
        results.append(
            {
                "sku": p.sku,
                "slug": p.slug,
                "name": p.name_pt,
                "brand": p.brand,
                "price": str(p.price),
                "thumb": img.image.url if img and img.image else "",
                "url": f"/catalogo/{p.slug}/",
            }
        )
    cache.set(key, results, CACHE_TTL)
    return results
