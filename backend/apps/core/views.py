"""Views base do core (health + home)."""

from django.http import JsonResponse
from django.views.generic import TemplateView


class HomeView(TemplateView):
    template_name = "core/home.html"


def health(request):
    """Healthcheck para Docker/CI — sem auth."""
    return JsonResponse({"status": "ok", "service": "techparts"})
