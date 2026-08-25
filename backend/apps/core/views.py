"""Views base do core (health + home + PWA)."""

from __future__ import annotations

from pathlib import Path

from django.conf import settings
from django.contrib.staticfiles.finders import find
from django.http import FileResponse, Http404, HttpRequest, JsonResponse
from django.urls import reverse
from django.views.decorators.csrf import csrf_exempt
from django.views.decorators.http import require_GET, require_http_methods
from django.views.generic import TemplateView

from apps.catalog.models import Brand, Category
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
        "subtitle": "Equipamentos e peças de reposição com vínculo de modelo",
        "image_key": HOME_CAT_HVAC_KEY,
        "wide": True,
        "slugs": ("ventiladores-teto", "ventiladores-mesa", "pecas-eletricas"),
    },
    {
        "title": "Cozinha",
        "subtitle": "Peças compatíveis a partir do manual do equipamento",
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
        ctx["filter_brands"] = list(
            Brand.objects.order_by("name").values_list("name", flat=True)[:40]
        )
        ctx["filter_categories"] = list(
            Category.objects.order_by("name").values("slug", "name")[:12]
        )
        ctx["filter_voltages"] = ["110V", "220V", "Bivolt"]
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


def _lowcode_authorized(request: HttpRequest):
    """Exige ``X-Lowcode-Secret`` configurado para expor o webhook."""
    import secrets as secrets_mod

    expected = getattr(settings, "LOWCODE_WEBHOOK_SECRET", "") or ""
    if not expected:
        return JsonResponse(
            {"error": "lowcode_secret_not_configured"},
            status=503,
        )
    got = request.headers.get("X-Lowcode-Secret", "")
    if not secrets_mod.compare_digest(got, expected):
        return JsonResponse({"error": "unauthorized"}, status=401)
    return None


@csrf_exempt
@require_http_methods(["GET", "POST"])
def lowcode_hook(request: HttpRequest) -> JsonResponse:
    """
    Snapshot para automação low-code (n8n/Make).

    Requer ``LOWCODE_WEBHOOK_SECRET`` e o header ``X-Lowcode-Secret``.
    Query ``?demo=1`` força ``alert_recommended`` (útil no n8n EasyPanel / vídeo).
    """
    denied = _lowcode_authorized(request)
    if denied is not None:
        return denied

    from apps.core.lowcode import snapshot_should_alert
    from apps.dashboard.services.monitoring import collect_monitoring

    snap = collect_monitoring(limit=5)
    failures = len(snap.failures)
    demo = (request.GET.get("demo") or "").strip().lower() in {"1", "true", "yes"}
    return JsonResponse(
        {
            "status": "ok",
            "service": "techparts",
            "queues": snap.queues,
            "failures_24h": failures,
            "alert_recommended": demo or snapshot_should_alert(snap.queues, failures),
            "demo": demo,
            "checked_at": snap.health.get("checked_at"),
        }
    )


@csrf_exempt
@require_http_methods(["POST"])
def lowcode_report(request: HttpRequest) -> JsonResponse:
    """Recebe o relatório do n8n e cria ``OpsAlert`` (saída observável no painel)."""
    denied = _lowcode_authorized(request)
    if denied is not None:
        return denied

    import json

    from pydantic import ValidationError

    from apps.dashboard.services.monitoring import ingest_lowcode_report

    try:
        raw = json.loads(request.body.decode("utf-8") or "{}")
    except json.JSONDecodeError:
        return JsonResponse({"error": "json_invalido"}, status=400)
    if not isinstance(raw, dict):
        return JsonResponse({"error": "json_objeto_esperado"}, status=400)
    try:
        alert = ingest_lowcode_report(raw, notify=True)
    except ValidationError as exc:
        return JsonResponse({"error": "payload_invalido", "detail": exc.errors()}, status=400)
    return JsonResponse(
        {
            "status": "ok",
            "alert_id": str(alert.pk),
            "title": alert.title,
            "panel": "/dashboard/monitoramento/",
        },
        status=201,
    )


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
