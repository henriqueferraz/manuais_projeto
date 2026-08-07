"""Testes Fase 8 — i18n, canais, assinatura, garantia, escala."""

from __future__ import annotations

import hashlib
import hmac
import json

import pytest
from django.core.management import call_command
from django.test import Client, override_settings
from django.urls import reverse

from apps.core.i18n import detect_text_locale, normalize_locale
from apps.partners.models import PartnerService
from apps.products.models import Product
from apps.subscriptions.models import Subscription, SubscriptionPlan
from apps.tickets.models import Ticket
from apps.warranty.models import WarrantyCode


def test_normalize_and_detect_locale():
    assert normalize_locale("en-US") == "en"
    assert detect_text_locale("how does the fan not work") == "en"
    assert detect_text_locale("el ventilador no gira como") == "es"
    assert detect_text_locale("ventilador não gira") == "pt-BR"


@pytest.mark.django_db
def test_catalog_lang_cookie(client: Client):
    response = client.get(reverse("catalog:list"), {"lang": "en"})
    assert response.status_code == 200
    assert response.cookies.get("tp_lang").value == "en"


@pytest.mark.django_db
@override_settings(
    WHATSAPP_MODE="mock", WHATSAPP_VERIFY_TOKEN="techparts-dev", AI_RATE_LIMIT="100/m"
)
def test_whatsapp_verify_and_inbound(client: Client):
    verify = client.get(
        reverse("channels:whatsapp_webhook"),
        {"hub.mode": "subscribe", "hub.verify_token": "techparts-dev", "hub.challenge": "abc123"},
    )
    assert verify.status_code == 200
    assert verify.content == b"abc123"

    payload = {"text": "ventilador faz barulho", "from": "5511999999999"}
    post = client.post(
        reverse("channels:whatsapp_webhook"),
        data=json.dumps(payload),
        content_type="application/json",
    )
    assert post.status_code == 200
    body = post.json()
    assert body["ok"] is True
    assert body["outbound"] == "mock"


@pytest.mark.django_db
@override_settings(WHATSAPP_MODE="mock", WHATSAPP_APP_SECRET="secret-wa", AI_RATE_LIMIT="100/m")
def test_whatsapp_rejects_bad_signature(client: Client):
    payload = b'{"text":"oi","from":"1"}'
    bad = client.post(
        reverse("channels:whatsapp_webhook"),
        data=payload,
        content_type="application/json",
        HTTP_X_HUB_SIGNATURE_256="sha256=deadbeef",
    )
    assert bad.status_code == 403

    digest = hmac.new(b"secret-wa", payload, hashlib.sha256).hexdigest()
    ok = client.post(
        reverse("channels:whatsapp_webhook"),
        data=payload,
        content_type="application/json",
        HTTP_X_HUB_SIGNATURE_256=f"sha256={digest}",
    )
    assert ok.status_code == 200


@pytest.mark.django_db
def test_subscription_mock_start(client: Client):
    plan = SubscriptionPlan.objects.create(
        code="basic",
        name="Básico",
        price_monthly="29.90",
        description="Preventiva",
    )
    response = client.post(reverse("subscriptions:plans"), {"plan_id": plan.pk, "email": "a@b.com"})
    assert response.status_code == 302
    assert Subscription.objects.filter(email="a@b.com", plan=plan).exists()


@pytest.mark.django_db
def test_partners_filter(client: Client):
    PartnerService.objects.create(name="TechFix SP", city="São Paulo", state="SP", active=True)
    PartnerService.objects.create(name="TechFix RJ", city="Rio", state="RJ", active=True)
    response = client.get(reverse("partners:list"), {"state": "SP"})
    assert response.status_code == 200
    assert b"TechFix SP" in response.content
    assert b"TechFix RJ" not in response.content


@pytest.mark.django_db
def test_warranty_qr_opens_ticket(client: Client):
    code = WarrantyCode.objects.create(sku="SKU-QR", label="Garantia VTE", active=True)
    response = client.post(
        reverse("warranty:claim", kwargs={"code_id": code.pk}),
        {
            "email": "cliente@example.com",
            "title": "Ruído",
            "description": "Motor com ruído metálico",
        },
    )
    assert response.status_code == 302
    ticket = Ticket.objects.get(email="cliente@example.com")
    assert ticket.origin == Ticket.Origin.QR
    assert ticket.equipment == "SKU-QR"


@pytest.mark.django_db
def test_seed_scale_catalog():
    call_command("seed_scale_catalog", count=6)
    assert Product.objects.filter(sku__startswith="SCL-").count() >= 6
