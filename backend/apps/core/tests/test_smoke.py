"""Smoke tests — R3 desde o primeiro PR de código (F2)."""

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
def test_home_renders_brand():
    client = Client()
    response = client.get(reverse("core:home"))
    assert response.status_code == 200
    assert b"TechParts AI" in response.content
    assert b"Industrial Precision" in response.content or b"precis" in response.content.lower()


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
    from django.http import HttpResponse
    from django.test import RequestFactory

    from apps.core.ratelimit import ai_rate_limit

    settings.AI_RATE_LIMIT = "2/m"

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
