"""Views de trocas/devoluções — cliente e operação."""

from __future__ import annotations

from django.contrib import messages
from django.contrib.auth.decorators import login_required, user_passes_test
from django.core.exceptions import ValidationError
from django.http import HttpRequest, HttpResponse, HttpResponseForbidden
from django.shortcuts import get_object_or_404, redirect, render
from django.views.decorators.http import require_http_methods, require_POST

from apps.orders.forms import ReturnProcessForm, ReturnRequestForm
from apps.orders.models import Order, ReturnRequest
from apps.orders.return_services import create_return_request, process_return


def _is_ops(user) -> bool:
    if not user.is_authenticated:
        return False
    if user.is_superuser or user.is_staff:
        return True
    return user.groups.filter(name__in=("admin", "operacao", "suporte")).exists()


def _can_view_return(request: HttpRequest, obj: ReturnRequest) -> bool:
    if _is_ops(request.user):
        return True
    if request.user.is_authenticated and obj.user_id == request.user.id:
        return True
    email = (request.GET.get("email") or request.POST.get("email") or "").strip()
    return bool(email and email.lower() == obj.email.lower())


@require_http_methods(["GET", "POST"])
def return_list(request: HttpRequest) -> HttpResponse:
    form = ReturnRequestForm(request.POST or None)
    if request.user.is_authenticated and not request.POST:
        form.fields["email"].initial = request.user.email or ""

    if request.method == "POST" and form.is_valid():
        order = Order.objects.filter(number__iexact=form.cleaned_data["order_number"]).first()
        if order is None:
            messages.error(request, "Pedido não encontrado.")
        elif order.email.lower() != form.cleaned_data["email"].lower():
            messages.error(request, "E-mail não confere com o pedido.")
        else:
            try:
                obj = create_return_request(
                    order=order,
                    email=form.cleaned_data["email"],
                    kind=form.cleaned_data["kind"],
                    reason=form.cleaned_data["reason"],
                    details=form.cleaned_data.get("details") or "",
                    user=request.user,
                )
                messages.success(request, "Solicitação registrada. Acompanhe o status abaixo.")
                return redirect("returns:detail", pk=obj.pk)
            except ValidationError as exc:
                messages.error(request, "; ".join(exc.messages))

    email = request.GET.get("email", "").strip()
    if request.user.is_authenticated:
        from django.db.models import Q

        qs = ReturnRequest.objects.filter(
            Q(user=request.user) | Q(email__iexact=request.user.email or "")
        ).select_related("order")
    elif email:
        qs = ReturnRequest.objects.filter(email__iexact=email).select_related("order")
    else:
        qs = ReturnRequest.objects.none()

    return render(
        request,
        "returns/list.html",
        {"form": form, "returns": qs[:50], "email": email},
    )


def return_detail(request: HttpRequest, pk) -> HttpResponse:
    obj = get_object_or_404(ReturnRequest.objects.select_related("order"), pk=pk)
    if not _can_view_return(request, obj):
        return HttpResponseForbidden("Acesso negado à solicitação.")

    process_form = ReturnProcessForm() if _is_ops(request.user) else None
    return render(
        request,
        "returns/detail.html",
        {"obj": obj, "process_form": process_form, "is_ops": _is_ops(request.user)},
    )


@login_required
@user_passes_test(_is_ops)
@require_http_methods(["GET"])
def returns_ops_panel(request: HttpRequest) -> HttpResponse:
    status = request.GET.get("status", "")
    qs = ReturnRequest.objects.select_related("order").all()
    if status:
        qs = qs.filter(status=status)
    return render(
        request,
        "returns/ops_panel.html",
        {
            "returns": qs[:100],
            "status": status,
            "status_choices": ReturnRequest.Status.choices,
        },
    )


@login_required
@user_passes_test(_is_ops)
@require_POST
def returns_process(request: HttpRequest, pk) -> HttpResponse:
    obj = get_object_or_404(ReturnRequest, pk=pk)
    form = ReturnProcessForm(request.POST)
    if not form.is_valid():
        messages.error(request, "Dados inválidos.")
        return redirect("returns:detail", pk=pk)
    try:
        process_return(
            obj,
            approve=bool(form.cleaned_data.get("approve")),
            staff_notes=form.cleaned_data.get("staff_notes") or "",
        )
        messages.success(request, f"Solicitação atualizada: {obj.get_status_display()}.")
    except ValidationError as exc:
        messages.error(request, "; ".join(exc.messages))
    return redirect("returns:detail", pk=pk)
