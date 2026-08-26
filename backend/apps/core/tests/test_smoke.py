"""Smoke tests — R3 desde o primeiro PR de código (F2)."""

import json

import pytest
from django.contrib.auth.models import Group, User
from django.test import Client
from django.urls import reverse


@pytest.mark.django_db
def test_health_ok():
    client = Client()
    response = client.get(reverse("core:health"))
    assert response.status_code == 200
    assert response.json()["status"] == "ok"
    assert "X-Request-ID" in response


@pytest.mark.django_db
def test_lowcode_hook_rejects_missing_secret(settings):
    settings.LOWCODE_WEBHOOK_SECRET = ""
    client = Client()
    response = client.get(reverse("core:lowcode_hook"))
    assert response.status_code == 503
    assert response.json()["error"] == "lowcode_secret_not_configured"


@pytest.mark.django_db
def test_lowcode_hook_requires_secret_when_configured(settings):
    settings.LOWCODE_WEBHOOK_SECRET = "n8n-dev-secret"
    client = Client()
    denied = client.get(reverse("core:lowcode_hook"))
    assert denied.status_code == 401
    ok = client.get(
        reverse("core:lowcode_hook"),
        HTTP_X_LOWCODE_SECRET="n8n-dev-secret",
    )
    assert ok.status_code == 200
    assert ok.json()["service"] == "techparts"


@pytest.mark.django_db
def test_lowcode_report_creates_ops_alert(settings):
    from apps.dashboard.models import OpsAlert

    settings.LOWCODE_WEBHOOK_SECRET = "n8n-dev-secret"
    client = Client()
    res = client.post(
        reverse("core:lowcode_report"),
        data=json.dumps(
            {
                "source": "n8n",
                "title": "Alerta ops (n8n)",
                "message": "Falhas 24h: 3",
                "failures_24h": 3,
                "queues": {"awaiting_review": 1},
                "severity": "warning",
            }
        ),
        content_type="application/json",
        HTTP_X_LOWCODE_SECRET="n8n-dev-secret",
    )
    assert res.status_code == 201
    body = res.json()
    assert body["status"] == "ok"
    assert OpsAlert.objects.filter(pk=body["alert_id"]).exists()
    alert = OpsAlert.objects.get(pk=body["alert_id"])
    assert alert.payload.get("source") == "n8n"
    assert "3" in alert.message or alert.payload.get("failures_24h") == 3


@pytest.mark.django_db
def test_lowcode_report_rejects_invalid_json(settings):
    settings.LOWCODE_WEBHOOK_SECRET = "n8n-dev-secret"
    client = Client()
    res = client.post(
        reverse("core:lowcode_report"),
        data="not-json",
        content_type="application/json",
        HTTP_X_LOWCODE_SECRET="n8n-dev-secret",
    )
    assert res.status_code == 400


@pytest.mark.django_db
def test_lowcode_snapshot_includes_alert_flag(settings):
    settings.LOWCODE_WEBHOOK_SECRET = "n8n-dev-secret"
    client = Client()
    body = client.get(
        reverse("core:lowcode_hook"),
        HTTP_X_LOWCODE_SECRET="n8n-dev-secret",
    ).json()
    assert "alert_recommended" in body
    assert body["alert_recommended"] in {True, False}


@pytest.mark.django_db
def test_lowcode_snapshot_demo_forces_alert(settings):
    settings.LOWCODE_WEBHOOK_SECRET = "n8n-dev-secret"
    client = Client()
    body = client.get(
        reverse("core:lowcode_hook"),
        {"demo": "1"},
        HTTP_X_LOWCODE_SECRET="n8n-dev-secret",
    ).json()
    assert body["demo"] is True
    assert body["alert_recommended"] is True


@pytest.mark.django_db
def test_home_renders_brand():
    client = Client()
    response = client.get(reverse("core:home"))
    assert response.status_code == 200
    assert b"TechParts AI" in response.content
    assert b"tp-home-hero" in response.content
    assert b"tp-topnav" in response.content
    assert b"Assistente" in response.content
    assert b"Compatibilidade" in response.content
    assert b"Assinaturas" in response.content
    assert b"tp-home-ai" in response.content
    assert b"tp-home-filters" in response.content
    assert b"home-filter-sort" in response.content
    assert b"price_desc" in response.content
    assert b"Produtos em destaque" in response.content
    assert b"Diagn" in response.content  # CTA diagnóstico
    assert b"catalogo" in response.content.lower() or b"Cat" in response.content
    assert b"tp-footer" in response.content


@pytest.mark.django_db
def test_login_page_uses_techparts_auth_shell():
    client = Client()
    response = client.get(reverse("two_factor:login"))
    assert response.status_code == 200
    body = response.content
    assert b"Provide a template named" not in body
    assert b"cdnjs.cloudflare.com" not in body
    assert b"tp-auth" in body
    assert b"Entrar na conta" in body
    assert b"TechParts AI" in body
    assert b"design-system/auth.css" in body


@pytest.mark.django_db
def test_home_featured_products_when_published():
    from decimal import Decimal

    from apps.catalog.models import Category
    from apps.products.models import Product, ProductTranslation

    cat = Category.objects.create(name="Ventiladores de teto", slug="ventiladores-teto")
    product = Product.objects.create(
        sku="HOME-01",
        brand="Mondial",
        model_code="H1",
        price=Decimal("99.90"),
        status=Product.Status.PUBLISHED,
        category=cat,
    )
    ProductTranslation.objects.create(product=product, locale="pt-BR", name="Peça home")

    client = Client()
    response = client.get(reverse("core:home"))
    assert response.status_code == 200
    assert b"HOME-01" in response.content
    assert b"Pe" in response.content and b"home" in response.content


@pytest.mark.django_db
def test_home_hero_carousel_when_slides_active():
    from apps.dashboard.models import HomeHeroSlide

    HomeHeroSlide.objects.create(
        badge="TECNOLOGIA AI",
        title="Precisao em Diagnostico",
        lead="IA cita o manual.",
        sort_order=1,
        is_active=True,
    )
    HomeHeroSlide.objects.create(
        title="Inativo nao aparece",
        is_active=False,
        sort_order=2,
    )

    client = Client()
    response = client.get(reverse("core:home"))
    assert response.status_code == 200
    assert b"tp-home-hero--carousel" in response.content
    assert b"Precisao em Diagnostico" in response.content
    assert b"TECNOLOGIA AI" in response.content
    assert b"Inativo nao aparece" not in response.content
    assert b"data-tp-hero-carousel" in response.content


@pytest.mark.django_db
def test_service_worker_served_at_root():
    client = Client()
    response = client.get(reverse("core:service_worker"))
    assert response.status_code == 200
    assert "javascript" in response["Content-Type"]
    assert response.get("Service-Worker-Allowed") == "/"
    if hasattr(response, "streaming_content"):
        body = b"".join(response.streaming_content)
    else:
        body = response.content
    assert b"tp-shell" in body or b"CACHE" in body


@pytest.mark.django_db
def test_bootstrap_rbac_creates_groups(settings):
    from django.core.management import call_command

    call_command("bootstrap_rbac")
    for name in settings.RBAC_GROUPS:
        assert Group.objects.filter(name=name).exists()


@pytest.mark.django_db
def test_mask_pii_redacts_email_and_sensitive_keys():
    from apps.core.logging import mask_pii

    event = mask_pii(None, "info", {"email": "a@b.com", "msg": "contato a@b.com", "password": "x"})
    assert event["email"] == "[REDACTED]"
    assert event["password"] == "[REDACTED]"
    assert "[EMAIL]" in event["msg"]


@pytest.mark.django_db
def test_ai_rate_limit_stub(settings):
    from django.core.cache import cache
    from django.http import HttpResponse
    from django.test import RequestFactory

    from apps.core.ratelimit import ai_rate_limit

    settings.AI_RATE_LIMIT = "2/m"
    cache.clear()

    @ai_rate_limit
    def view(request):
        return HttpResponse("ok")

    factory = RequestFactory()
    req = factory.get("/ai/")
    assert view(req).status_code == 200
    assert view(req).status_code == 200
    assert view(req).status_code == 429


@pytest.mark.django_db
def test_sensitive_action_log_on_login():
    from apps.accounts.models import SensitiveActionLog

    user = User.objects.create_user(username="staff1", password="pass12345")
    client = Client()
    assert client.login(username="staff1", password="pass12345")
    assert SensitiveActionLog.objects.filter(
        action=SensitiveActionLog.Action.LOGIN, actor=user
    ).exists()
