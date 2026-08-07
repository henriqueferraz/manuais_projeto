"""Views do dashboard de insights e monitoramento (F7)."""

from __future__ import annotations

from django.contrib import messages
from django.contrib.auth.decorators import login_required, user_passes_test
from django.http import HttpRequest, HttpResponse, JsonResponse
from django.shortcuts import get_object_or_404, redirect, render
from django.utils import timezone
from django.views.decorators.http import require_GET, require_http_methods, require_POST

from apps.dashboard.models import OpsAlert
from apps.dashboard.services.metrics import collect_insights
from apps.dashboard.services.monitoring import collect_monitoring, simulate_incident


def _is_ops(user) -> bool:
    if not user.is_authenticated:
        return False
    if user.is_superuser or user.is_staff:
        return True
    return user.groups.filter(name__in=("admin", "suporte", "revisao_catalogo")).exists()


@login_required
@user_passes_test(_is_ops)
@require_GET
def insights(request: HttpRequest) -> HttpResponse:
    try:
        days = int(request.GET.get("days") or 30)
    except (TypeError, ValueError):
        days = 30
    days = days if days in {7, 30, 90} else 30
    payload = collect_insights(days=days)
    return render(
        request,
        "dashboard/insights.html",
        {
            "insights": payload,
            "days": days,
            "page_title": "Dashboard de insights",
        },
    )


@login_required
@user_passes_test(_is_ops)
@require_GET
def monitoring(request: HttpRequest) -> HttpResponse:
    snap = collect_monitoring()
    return render(
        request,
        "dashboard/monitoring.html",
        {
            "snap": snap,
            "page_title": "Monitoramento",
        },
    )


@login_required
@user_passes_test(_is_ops)
@require_POST
def acknowledge_alert(request: HttpRequest, alert_id) -> HttpResponse:
    alert = get_object_or_404(OpsAlert, pk=alert_id)
    alert.acknowledged = True
    alert.acknowledged_by = request.user
    alert.acknowledged_at = timezone.now()
    alert.save(update_fields=["acknowledged", "acknowledged_by", "acknowledged_at", "updated_at"])
    messages.success(request, "Alerta reconhecido.")
    return redirect("dashboard:monitoring")


@login_required
@user_passes_test(_is_ops)
@require_http_methods(["POST"])
def simulate_incident_view(request: HttpRequest) -> HttpResponse:
    alert = simulate_incident()
    messages.warning(request, f"Incidente simulado criado: {alert.title}")
    if request.headers.get("Accept") == "application/json":
        return JsonResponse({"ok": True, "alert_id": str(alert.pk)})
    return redirect("dashboard:monitoring")
