from django.contrib import messages
from django.contrib.auth.decorators import login_required, user_passes_test
from django.http import HttpRequest, HttpResponse
from django.shortcuts import get_object_or_404, redirect, render
from django.views.decorators.http import require_GET, require_http_methods

from apps.tickets.models import Ticket
from apps.tickets.services import create_ticket
from apps.warranty.models import WarrantyCode


def _is_ops(user) -> bool:
    return user.is_authenticated and (user.is_staff or user.is_superuser)


@require_http_methods(["GET", "POST"])
def claim(request: HttpRequest, code_id) -> HttpResponse:
    code = get_object_or_404(WarrantyCode, pk=code_id, active=True)
    if request.method == "POST":
        email = (request.POST.get("email") or "").strip()
        title = (request.POST.get("title") or "Garantia via QR").strip()
        description = (request.POST.get("description") or "").strip()
        if not email or not description:
            messages.error(request, "E-mail e descrição são obrigatórios.")
        else:
            ticket = create_ticket(
                email=email,
                title=title,
                description=description,
                equipment=code.sku or code.label,
                origin=Ticket.Origin.QR,
                user=request.user if request.user.is_authenticated else None,
            )
            messages.success(request, f"Chamado {ticket.code} aberto pela garantia QR.")
            return redirect("tickets:detail", code=ticket.code)
    return render(request, "warranty/claim.html", {"code": code})


@login_required
@user_passes_test(_is_ops)
@require_GET
def qr_png(request: HttpRequest, code_id) -> HttpResponse:
    code = get_object_or_404(WarrantyCode, pk=code_id)
    absolute = request.build_absolute_uri(code.public_path())
    return HttpResponse(code.qr_png_bytes(absolute), content_type="image/png")
