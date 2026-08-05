"""Views de chamados — cliente e painel suporte."""

from __future__ import annotations

from django.contrib import messages
from django.contrib.auth.decorators import login_required, user_passes_test
from django.http import HttpRequest, HttpResponse, HttpResponseForbidden
from django.shortcuts import get_object_or_404, redirect, render
from django.urls import reverse
from django.views.decorators.http import require_http_methods

from apps.tickets.forms import TicketCreateForm, TicketStatusForm
from apps.tickets.models import Ticket
from apps.tickets.services import create_ticket, update_ticket_status


def _is_support(user) -> bool:
    if not user.is_authenticated:
        return False
    if user.is_superuser or user.is_staff:
        return True
    return user.groups.filter(name__in=("admin", "suporte")).exists()


def _can_view_ticket(request: HttpRequest, ticket: Ticket) -> bool:
    if _is_support(request.user):
        return True
    if request.user.is_authenticated and ticket.user_id == request.user.id:
        return True
    email = (request.GET.get("email") or request.POST.get("email") or "").strip()
    return bool(email and email.lower() == ticket.email.lower())


@require_http_methods(["GET", "POST"])
def ticket_list(request: HttpRequest) -> HttpResponse:
    form = TicketCreateForm(request.POST or None)
    if request.user.is_authenticated and not request.POST:
        form.fields["email"].initial = request.user.email or ""

    if request.method == "POST" and form.is_valid():
        ticket = create_ticket(
            email=form.cleaned_data["email"],
            title=form.cleaned_data["title"],
            description=form.cleaned_data["description"],
            equipment=form.cleaned_data.get("equipment") or "",
            user=request.user,
            priority=form.cleaned_data["priority"],
        )
        messages.success(request, f"Chamado {ticket.code} aberto.")
        return redirect(
            f"{reverse('tickets:detail', kwargs={'code': ticket.code})}?email={ticket.email}"
        )

    email = request.GET.get("email", "").strip()
    if request.user.is_authenticated:
        from django.db.models import Q

        qs = Ticket.objects.filter(
            Q(user=request.user) | Q(email__iexact=request.user.email or "")
        ).distinct()
    elif email:
        qs = Ticket.objects.filter(email__iexact=email)
    else:
        qs = Ticket.objects.none()

    context = {"tickets": qs[:50], "form": form, "email": email}
    if request.headers.get("HX-Request") and request.method == "GET":
        return render(request, "tickets/partials/list.html", context)
    return render(request, "tickets/list.html", context)


def ticket_detail(request: HttpRequest, code: str) -> HttpResponse:
    ticket = get_object_or_404(
        Ticket.objects.prefetch_related("events", "attachments"),
        code=code,
    )
    if not _can_view_ticket(request, ticket):
        return HttpResponseForbidden("Acesso negado ao chamado.")

    status_form = TicketStatusForm(initial={"status": ticket.status})
    return render(
        request,
        "tickets/detail.html",
        {
            "ticket": ticket,
            "status_form": status_form,
            "is_support": _is_support(request.user),
        },
    )


@login_required
@user_passes_test(_is_support)
def support_panel(request: HttpRequest) -> HttpResponse:
    status = request.GET.get("status", "")
    qs = Ticket.objects.select_related("assigned_to").order_by("-sla_breached", "sla_due_at")
    if status:
        qs = qs.filter(status=status)
    return render(
        request,
        "tickets/support_panel.html",
        {
            "tickets": qs[:100],
            "status": status,
            "status_choices": Ticket.Status.choices,
            "breached_count": Ticket.objects.filter(sla_breached=True)
            .exclude(status__in=[Ticket.Status.RESOLVED, Ticket.Status.CLOSED])
            .count(),
        },
    )


@login_required
@user_passes_test(_is_support)
@require_http_methods(["POST"])
def support_update_status(request: HttpRequest, code: str) -> HttpResponse:
    ticket = get_object_or_404(Ticket, code=code)
    form = TicketStatusForm(request.POST)
    if form.is_valid():
        update_ticket_status(
            ticket,
            new_status=form.cleaned_data["status"],
            note=form.cleaned_data.get("note") or "",
            author=request.user,
        )
        messages.success(request, "Status atualizado.")
    else:
        messages.error(request, "Dados inválidos.")
    return redirect("tickets:detail", code=ticket.code)
