"""Views do catálogo (listagem htmx, PDP, autocomplete)."""

from __future__ import annotations

from pathlib import Path

from django.core.paginator import Paginator
from django.http import FileResponse, Http404, HttpRequest, HttpResponse, JsonResponse
from django.shortcuts import get_object_or_404, redirect, render
from django.views.decorators.http import require_GET

from apps.catalog.services import (
    CATALOG_SORT_CHOICES,
    autocomplete,
    cached_filter_count,
    filter_catalog,
)
from apps.compatibility.services import compat_labels_for_product
from apps.products.image_validation import gallery_images_queryset
from apps.products.models import Product
from apps.tickets.services import cross_sell_for_product


def _filter_params(request: HttpRequest) -> dict:
    from apps.core.i18n import resolve_locale

    sort = (request.GET.get("sort") or "").strip().lower()
    allowed = {key for key, _ in CATALOG_SORT_CHOICES}
    if sort not in allowed:
        sort = ""

    return {
        "q": request.GET.get("q", "").strip(),
        "category": request.GET.get("category", "").strip(),
        "voltage": request.GET.get("voltage", "").strip(),
        "model": request.GET.get("model", "").strip(),
        "brand": request.GET.get("brand", "").strip(),
        "compat_model": request.GET.get("compat_model", "").strip(),
        "sort": sort,
        "locale": resolve_locale(request),
    }


@require_GET
def product_list(request: HttpRequest) -> HttpResponse:
    from apps.core.i18n import COOKIE

    params = _filter_params(request)
    locale = params["locale"]
    qs = filter_catalog(**params)
    cache_key = "catalog:count:" + "&".join(f"{k}={v}" for k, v in sorted(params.items()) if v)
    total = cached_filter_count(cache_key, qs)

    paginator = Paginator(qs, 12)
    page = paginator.get_page(request.GET.get("page") or 1)

    context = {
        "products": page,
        "params": params,
        "total": total,
        "locale": locale,
        "voltages": ["110V", "220V", "Bivolt"],
        "categories": _category_choices(),
        "sort_choices": CATALOG_SORT_CHOICES,
    }

    if request.headers.get("HX-Request"):
        response = render(request, "catalog/partials/product_grid.html", context)
    else:
        response = render(request, "catalog/product_list.html", context)
    if request.GET.get("lang"):
        response.set_cookie(COOKIE, locale, max_age=60 * 60 * 24 * 365)
    return response


def _manual_for_product(product: Product):
    """Manual vinculado ao produto (FK direta ou linked_product)."""
    from apps.manuals.models import Manual

    if product.manual_id:
        return product.manual
    return (
        Manual.objects.filter(linked_product_id=product.pk).exclude(file="").order_by("-id").first()
    )


@require_GET
def product_detail(request: HttpRequest, slug: str) -> HttpResponse:
    from apps.core.i18n import resolve_locale

    product = get_object_or_404(
        Product.objects.select_related("category", "stock", "manual").prefetch_related(
            "translations", "images"
        ),
        slug=slug,
        status=Product.Status.PUBLISHED,
    )
    locale = resolve_locale(request)
    manual = _manual_for_product(product)
    return render(
        request,
        "catalog/product_detail.html",
        {
            "product": product,
            "locale": locale,
            "compat_labels": compat_labels_for_product(product),
            "images": list(gallery_images_queryset(product)),
            "cross_sell": cross_sell_for_product(product),
            "has_manual": bool(
                manual and (getattr(manual, "file", None) or getattr(manual, "storage_key", ""))
            ),
        },
    )


@require_GET
def product_manual_download(request: HttpRequest, slug: str) -> HttpResponse:
    """Download do manual PDF do produto (URL assinada ou arquivo local)."""
    from apps.manuals.storage import signed_url

    product = get_object_or_404(
        Product.objects.select_related("manual"),
        slug=slug,
        status=Product.Status.PUBLISHED,
    )
    manual = _manual_for_product(product)
    if manual is None:
        raise Http404("Manual não disponível para este produto.")

    storage_key = (manual.storage_key or "").strip() or (
        getattr(manual.file, "name", "") if manual.file else ""
    )
    if not storage_key:
        raise Http404("Arquivo do manual não encontrado.")

    url = signed_url(storage_key)
    if url and "://" in url:
        return redirect(url)

    if not manual.file:
        raise Http404("Arquivo do manual não encontrado.")
    filename = Path(manual.original_filename or storage_key).name or f"{product.sku}-manual.pdf"
    if not filename.lower().endswith(".pdf"):
        filename = f"{filename}.pdf"
    handle = manual.file.open("rb")
    return FileResponse(
        handle,
        as_attachment=True,
        filename=filename,
        content_type="application/pdf",
    )


@require_GET
def search_autocomplete(request: HttpRequest) -> HttpResponse:
    q = request.GET.get("q", "")
    results = autocomplete(q)
    if request.headers.get("HX-Request") or request.GET.get("format") != "json":
        return render(request, "catalog/partials/autocomplete.html", {"results": results})
    return JsonResponse({"results": results})


def _category_choices():
    from apps.catalog.models import Category

    return list(Category.objects.order_by("name").values("slug", "name"))
