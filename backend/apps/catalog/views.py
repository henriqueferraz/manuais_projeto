"""Views do catálogo (listagem htmx, PDP, autocomplete)."""

from __future__ import annotations

from django.core.paginator import Paginator
from django.http import HttpRequest, HttpResponse, JsonResponse
from django.shortcuts import get_object_or_404, render
from django.views.decorators.http import require_GET

from apps.catalog.services import autocomplete, cached_filter_count, filter_catalog
from apps.compatibility.services import compat_labels_for_product
from apps.products.models import Product
from apps.tickets.services import cross_sell_for_product


def _filter_params(request: HttpRequest) -> dict:
    from apps.core.i18n import resolve_locale

    return {
        "q": request.GET.get("q", "").strip(),
        "category": request.GET.get("category", "").strip(),
        "voltage": request.GET.get("voltage", "").strip(),
        "model": request.GET.get("model", "").strip(),
        "brand": request.GET.get("brand", "").strip(),
        "compat_model": request.GET.get("compat_model", "").strip(),
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
    }

    if request.headers.get("HX-Request"):
        response = render(request, "catalog/partials/product_grid.html", context)
    else:
        response = render(request, "catalog/product_list.html", context)
    if request.GET.get("lang"):
        response.set_cookie(COOKIE, locale, max_age=60 * 60 * 24 * 365)
    return response


@require_GET
def product_detail(request: HttpRequest, slug: str) -> HttpResponse:
    from apps.core.i18n import resolve_locale

    product = get_object_or_404(
        Product.objects.select_related("category", "stock").prefetch_related(
            "translations", "images"
        ),
        slug=slug,
        status=Product.Status.PUBLISHED,
    )
    locale = resolve_locale(request)
    return render(
        request,
        "catalog/product_detail.html",
        {
            "product": product,
            "locale": locale,
            "compat_labels": compat_labels_for_product(product),
            "images": list(product.images.all()),
            "cross_sell": cross_sell_for_product(product),
        },
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
