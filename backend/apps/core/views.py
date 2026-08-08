"""Views base do core (health + home + PWA)."""

from __future__ import annotations

from pathlib import Path

from django.contrib.staticfiles.finders import find
from django.http import FileResponse, Http404, HttpRequest, JsonResponse
from django.urls import reverse
from django.views.decorators.http import require_GET
from django.views.generic import TemplateView

from apps.catalog.models import Category
from apps.catalog.services import published_products
from apps.core.branding import (
    HOME_CAT_HVAC_KEY,
    HOME_CAT_KITCHEN_KEY,
    branding_image_url,
)
from apps.dashboard.models import HomeHeroSlide

# Bento da home — slugs preferidos (seed_beta / seed_scale_catalog); fallback = catálogo.
_HOME_CATEGORY_TILES = (
    {
        "title": "Linha HVAC",
        "subtitle": "Compressores, placas e filtros de alta precisão",
        "image_key": HOME_CAT_HVAC_KEY,
        "wide": True,
        "slugs": ("ventiladores-teto", "ventiladores-mesa", "pecas-eletricas"),
    },
    {
        "title": "Cozinha",
        "subtitle": "Sensores de temperatura e motores",
        "image_key": HOME_CAT_KITCHEN_KEY,
        "wide": False,
        "slugs": ("liquidificadores", "aspiradores", "ferros"),
    },
)


class HomeView(TemplateView):
    template_name = "core/home.html"
    featured_limit = 6

    def get_context_data(self, **kwargs):
        ctx = super().get_context_data(**kwargs)
        qs = published_products()
        total = qs.count()
        featured = list(qs.order_by("-published_at", "-updated_at")[: self.featured_limit])
        ctx["featured_products"] = featured
        ctx["featured_total"] = total
        ctx["featured_shown"] = len(featured)
        ctx["category_tiles"] = self._category_tiles()
        ctx["hero_slides"] = list(
            HomeHeroSlide.objects.filter(is_active=True).order_by("sort_order", "id")
        )
        return ctx

    def _category_tiles(self) -> list[dict]:
        tiles: list[dict] = []
        catalog_url = reverse("catalog:list")
        for spec in _HOME_CATEGORY_TILES:
            href = catalog_url
            for slug in spec["slugs"]:
                if Category.objects.filter(slug=slug).exists():
                    href = f"{catalog_url}?category={slug}"
                    break
            tiles.append(
                {
                    "title": spec["title"],
                    "subtitle": spec["subtitle"],
                    "image_url": branding_image_url(spec["image_key"]),
                    "wide": spec["wide"],
                    "href": href,
                }
            )
        return tiles


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
