from django.http import HttpRequest, HttpResponse
from django.shortcuts import render
from django.views.decorators.http import require_GET

from apps.partners.models import PartnerService


@require_GET
def partner_list(request: HttpRequest) -> HttpResponse:
    state = (request.GET.get("state") or "").strip().upper()
    city = (request.GET.get("city") or "").strip()
    qs = PartnerService.objects.filter(active=True)
    if state:
        qs = qs.filter(state=state)
    if city:
        qs = qs.filter(city__icontains=city)
    return render(
        request,
        "partners/list.html",
        {"partners": qs[:100], "state": state, "city": city},
    )
