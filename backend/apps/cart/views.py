"""Views do carrinho (htmx)."""

from __future__ import annotations

from django.contrib import messages
from django.core.exceptions import ValidationError
from django.http import HttpRequest, HttpResponse
from django.shortcuts import get_object_or_404, redirect, render
from django.views.decorators.http import require_http_methods, require_POST

from apps.cart.services import (
    add_to_cart,
    cart_totals,
    get_or_create_cart,
    remove_cart_item,
    update_cart_item,
)
from apps.products.models import Product


def _cart_response(request: HttpRequest, *, partial: bool = False) -> HttpResponse:
    cart = get_or_create_cart(request)
    totals = cart_totals(cart)
    context = {"cart": cart, **totals}
    template = (
        "cart/partials/cart_panel.html"
        if partial or request.headers.get("HX-Request")
        else "cart/cart.html"
    )
    return render(request, template, context)


@require_http_methods(["GET"])
def cart_detail(request: HttpRequest) -> HttpResponse:
    return _cart_response(request)


@require_POST
def cart_add(request: HttpRequest) -> HttpResponse:
    product = get_object_or_404(Product, pk=request.POST.get("product_id"))
    try:
        qty = int(request.POST.get("quantity") or 1)
    except (TypeError, ValueError):
        qty = 1
    try:
        add_to_cart(request, product, qty)
        messages.success(request, f"{product.name_pt} adicionado ao carrinho.")
    except ValidationError as exc:
        messages.error(request, "; ".join(exc.messages))

    if request.headers.get("HX-Request"):
        cart = get_or_create_cart(request)
        totals = cart_totals(cart)
        response = render(
            request,
            "cart/partials/toast.html",
            {"cart": cart, **totals},
        )
        response["HX-Trigger"] = "cartUpdated"
        return response
    return redirect("cart:detail")


@require_POST
def cart_update(request: HttpRequest) -> HttpResponse:
    product_id = request.POST.get("product_id")
    try:
        qty = int(request.POST.get("quantity") or 0)
        update_cart_item(request, int(product_id), qty)
    except (TypeError, ValueError):
        messages.error(request, "Dados inválidos.")
    except ValidationError as exc:
        messages.error(request, "; ".join(exc.messages))

    if request.headers.get("HX-Request"):
        return _cart_response(request, partial=True)
    return redirect("cart:detail")


@require_POST
def cart_remove(request: HttpRequest) -> HttpResponse:
    try:
        remove_cart_item(request, int(request.POST.get("product_id")))
        messages.info(request, "Item removido.")
    except (TypeError, ValueError):
        messages.error(request, "Item inválido.")

    if request.headers.get("HX-Request"):
        return _cart_response(request, partial=True)
    return redirect("cart:detail")
