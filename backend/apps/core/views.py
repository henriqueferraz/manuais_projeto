"""Views base do core (health + home + PWA)."""

from __future__ import annotations

from pathlib import Path

from django.contrib.staticfiles.finders import find
from django.http import FileResponse, Http404, HttpRequest, JsonResponse
from django.views.decorators.http import require_GET
from django.views.generic import TemplateView


class HomeView(TemplateView):
    template_name = "core/home.html"


def health(request):
    """Healthcheck para Docker/CI — sem auth."""
    return JsonResponse({"status": "ok", "service": "techparts"})


@require_GET
def service_worker(request: HttpRequest) -> FileResponse:
    """Serve /sw.js na raiz para scope correto do PWA (ADR-0006 / B-008)."""
    path = find("pwa/sw.js")
    if not path:
        raise Http404("service worker não encontrado")
    response = FileResponse(Path(path).open("rb"), content_type="application/javascript")
    response["Service-Worker-Allowed"] = "/"
    response["Cache-Control"] = "no-cache"
    return response
