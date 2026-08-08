"""Verificador de compatibilidade + gestão interna."""

from __future__ import annotations

from django.contrib import messages
from django.contrib.auth.decorators import login_required, user_passes_test
from django.http import HttpRequest, HttpResponse
from django.shortcuts import redirect, render
from django.views.decorators.http import require_http_methods

from apps.compatibility.forms import CompatibilityForm
from apps.compatibility.models import Compatibility
from apps.compatibility.services import parts_for_equipment
from apps.dashboard.views import products_edit, products_list


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


# Aliases legados → dashboard Estoque e produtos
product_ops_list = products_list
product_ops_edit = products_edit


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
