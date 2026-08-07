"""Testes do dashboard F7."""

from __future__ import annotations

from decimal import Decimal

import pytest
from django.contrib.auth import get_user_model
from django.core import mail
from django.core.files.base import ContentFile
from django.test import Client
from django.urls import reverse

from apps.ai.models import ChatFeedback, ChatMessage, ChatSession
from apps.dashboard.models import OpsAlert
from apps.dashboard.services.metrics import collect_insights
from apps.dashboard.services.monitoring import collect_monitoring, simulate_incident
from apps.manuals.models import ExtractionLog, Manual
from apps.orders.models import Order
from apps.tickets.models import Ticket, TicketEvent

User = get_user_model()


@pytest.fixture
def staff_user(db):
    return User.objects.create_user(
        username="ops",
        email="ops@example.com",
        password="x",
        is_staff=True,
    )


@pytest.mark.django_db
def test_insights_four_areas(staff_user):
    session = ChatSession.objects.create(anonymous_key="d7")
    ChatMessage.objects.create(
        session=session,
        role=ChatMessage.Role.USER,
        content="Qual o capacitor de partida?",
    )
    asst = ChatMessage.objects.create(
        session=session,
        role=ChatMessage.Role.ASSISTANT,
        content="Com base no manual...",
        found_in_manual=True,
        cost_estimate=Decimal("0.002"),
        tokens_in=10,
        tokens_out=20,
    )
    ChatFeedback.objects.create(message=asst, vote=ChatFeedback.Vote.UP)

    ticket = Ticket.objects.create(
        code="TK-TEST-1",
        email="c@ex.com",
        title="Barulho",
        description="faz barulho",
        origin=Ticket.Origin.CHAT,
        status=Ticket.Status.RESOLVED,
    )
    TicketEvent.objects.create(
        ticket=ticket,
        status_from=Ticket.Status.OPEN,
        status_to=Ticket.Status.RESOLVED,
        note="ok",
    )

    Order.objects.create(
        number="TP-TEST-1",
        email="c@ex.com",
        shipping_name="A",
        shipping_cep="01310100",
        shipping_street="R",
        shipping_number="1",
        shipping_district="B",
        shipping_city="SP",
        shipping_state="SP",
        subtotal=Decimal("100"),
        total=Decimal("100"),
        attribution_source=Order.AttributionSource.DIAGNOSIS,
        chat_session=session,
    )

    manual = Manual(
        original_filename="x.pdf",
        mime_type="application/pdf",
        scan_status=Manual.ScanStatus.SKIPPED,
    )
    manual.file.save("x.pdf", ContentFile(b"%PDF-1.4\n%%EOF\n"), save=False)
    manual.compute_and_set_sha256(b"%PDF-1.4\n%%EOF\n")
    manual.save()
    ExtractionLog.objects.create(
        manual=manual,
        status=ExtractionLog.Status.APPROVED,
        cost_estimate=Decimal("0.01"),
    )

    payload = collect_insights(days=30)
    assert payload.chat["sessions"] >= 1
    assert payload.chat["feedback_up"] >= 1
    assert payload.tickets["total"] >= 1
    assert payload.sales_ai["ai_influenced_orders"] >= 1
    assert payload.ai_cost["total_usd"] > 0

    client = Client()
    client.force_login(staff_user)
    res = client.get(reverse("dashboard:insights"))
    assert res.status_code == 200
    body = res.content.decode()
    assert "Chat / RAG" in body
    assert "Chamados" in body
    assert "Vendas influenciadas" in body
    assert "Custo de IA" in body


@pytest.mark.django_db
def test_monitoring_simulated_incident_appears(staff_user, settings):
    settings.OPS_ALERT_EMAILS = ["ops@example.com"]
    settings.EMAIL_BACKEND = "django.core.mail.backends.locmem.EmailBackend"
    mail.outbox.clear()

    alert = simulate_incident(title="Incidente simulado teste")
    assert alert.pk
    assert OpsAlert.objects.filter(pk=alert.pk, acknowledged=False).exists()
    assert mail.outbox  # e-mail de alerta

    snap = collect_monitoring()
    assert any(a["title"] == "Incidente simulado teste" for a in snap.alerts)

    client = Client()
    client.force_login(staff_user)
    res = client.get(reverse("dashboard:monitoring"))
    assert res.status_code == 200
    assert b"Incidente simulado teste" in res.content

    res2 = client.post(reverse("dashboard:simulate_incident"))
    assert res2.status_code in (302, 200)


@pytest.mark.django_db
def test_insights_requires_staff(client):
    res = client.get(reverse("dashboard:insights"))
    assert res.status_code in (302, 301)
