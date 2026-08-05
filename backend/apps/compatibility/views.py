"""Verificador de compatibilidade + gestão interna."""

from __future__ import annotations

from django.contrib import messages
from django.contrib.auth.decorators import login_required, user_passes_test
from django.http import HttpRequest, HttpResponse
from django.shortcuts import get_object_or_404, redirect, render
from django.views.decorators.http import require_http_methods

from apps.catalog.models import Category
from apps.compatibility.forms import CompatibilityForm, InternalProductForm
from apps.compatibility.models import Compatibility
from apps.compatibility.services import parts_for_equipment
from apps.products.models import Product, ProductTranslation, Stock


def _staff_ops(user) -> bool:
    if not user.is_authenticated:
        return False
    if user.is_superuser or user.is_staff:
        return True
    return user.groups.filter(name__in=("admin", "revisao_catalogo")).exists()


@require_http_methods(["GET", "POST"])
def compatibility_checker(request: HttpRequest) -> HttpResponse:
    brand = request.POST.get("brand") or request.GET.get("brand", "")
    model = request.POST.get("model") or request.GET.get("model", "")
    parts = []
    searched = False
    if brand or model:
        searched = True
        parts = list(parts_for_equipment(brand=brand, model=model))

    context = {
        "brand": brand,
        "model": model,
        "parts": parts,
        "searched": searched,
    }
    if request.headers.get("HX-Request") and request.method == "POST":
        return render(request, "compatibility/partials/results.html", context)
    return render(request, "compatibility/checker.html", context)


@login_required
@user_passes_test(_staff_ops)
def product_ops_list(request: HttpRequest) -> HttpResponse:
    status = request.GET.get("status", "")
    qs = Product.objects.select_related("category", "stock").order_by("-updated_at")
    if status:
        qs = qs.filter(status=status)
    return render(
        request,
        "compatibility/ops_product_list.html",
        {"products": qs[:100], "status": status, "status_choices": Product.Status.choices},
    )


@login_required
@user_passes_test(_staff_ops)
@require_http_methods(["GET", "POST"])
def product_ops_edit(request: HttpRequest, pk: int | None = None) -> HttpResponse:
    product = get_object_or_404(Product, pk=pk) if pk else None
    initial = {}
    if product:
        tr = product.translations.filter(locale="pt-BR").first()
        stock = None
        try:
            stock = product.stock
        except Stock.DoesNotExist:
            stock = None
        initial = {
            "sku": product.sku,
            "brand": product.brand,
            "model_code": product.model_code,
            "name": tr.name if tr else "",
            "description": tr.description if tr else "",
            "price": product.price,
            "voltage": product.voltage,
            "product_kind": product.product_kind,
            "status": product.status,
            "category": product.category_id,
            "quantity_available": stock.quantity_available if stock else 0,
            "minimum_alert": stock.minimum_alert if stock else 2,
        }

    form = InternalProductForm(request.POST or None, initial=initial)
    if request.method == "POST" and form.is_valid():
        data = form.cleaned_data
        if product is None:
            product = Product(sku=data["sku"])
        product.sku = data["sku"]
        product.brand = data["brand"]
        product.model_code = data["model_code"]
        product.price = data["price"]
        product.voltage = data["voltage"]
        product.product_kind = data["product_kind"]
        product.status = data["status"]
        product.category = data["category"]
        product.save()
        ProductTranslation.objects.update_or_create(
            product=product,
            locale="pt-BR",
            defaults={"name": data["name"], "description": data["description"]},
        )
        stock, _ = Stock.objects.get_or_create(product=product)
        stock.quantity_available = data["quantity_available"]
        stock.minimum_alert = data["minimum_alert"]
        stock.save()
        messages.success(request, f"Produto {product.sku} salvo.")
        return redirect("compatibility:ops_list")

    return render(
        request,
        "compatibility/ops_product_form.html",
        {"form": form, "product": product, "categories": Category.objects.all()},
    )


@login_required
@user_passes_test(_staff_ops)
@require_http_methods(["GET", "POST"])
def compatibility_ops(request: HttpRequest) -> HttpResponse:
    form = CompatibilityForm(request.POST or None)
    if request.method == "POST" and form.is_valid():
        form.save()
        messages.success(request, "Compatibilidade registrada.")
        return redirect("compatibility:ops_compat")
    rows = Compatibility.objects.select_related("part_product").order_by("-updated_at")[:50]
    return render(
        request,
        "compatibility/ops_compat.html",
        {"form": form, "rows": rows},
    )
