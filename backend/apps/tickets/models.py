"""Chamados técnicos (F4c)."""

from __future__ import annotations

import uuid
from datetime import timedelta

from django.conf import settings
from django.db import models
from django.utils import timezone
from simple_history.models import HistoricalRecords


def default_sla_due():
    hours = int(getattr(settings, "TICKET_SLA_HOURS", 24))
    return timezone.now() + timedelta(hours=hours)


class Ticket(models.Model):
    class Status(models.TextChoices):
        OPEN = "open", "Aberto"
        IN_ANALYSIS = "in_analysis", "Em Análise"
        WAITING_PART = "waiting_part", "Aguardando Peça"
        RESOLVED = "resolved", "Resolvido"
        CLOSED = "closed", "Fechado"

    class Priority(models.TextChoices):
        LOW = "low", "Normal"
        MEDIUM = "medium", "Média"
        HIGH = "high", "Alta"

    class Origin(models.TextChoices):
        SITE = "site", "Site"
        CHAT = "chat", "Chat IA"
        EMAIL = "email", "E-mail"
        INTERNAL = "internal", "Interno"
        WHATSAPP = "whatsapp", "WhatsApp"
        QR = "qr", "QR Garantia"

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    code = models.CharField(max_length=24, unique=True, db_index=True)
    user = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        null=True,
        blank=True,
        on_delete=models.SET_NULL,
        related_name="tickets",
    )
    email = models.EmailField()
    title = models.CharField(max_length=200)
    description = models.TextField()
    equipment = models.CharField(max_length=120, blank=True)
    status = models.CharField(
        max_length=32,
        choices=Status.choices,
        default=Status.OPEN,
        db_index=True,
    )
    priority = models.CharField(
        max_length=16,
        choices=Priority.choices,
        default=Priority.MEDIUM,
    )
    origin = models.CharField(
        max_length=16,
        choices=Origin.choices,
        default=Origin.SITE,
    )
    order = models.ForeignKey(
        "orders.Order",
        null=True,
        blank=True,
        on_delete=models.SET_NULL,
        related_name="tickets",
    )
    assigned_to = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        null=True,
        blank=True,
        on_delete=models.SET_NULL,
        related_name="assigned_tickets",
    )
    sla_due_at = models.DateTimeField(default=default_sla_due)
    sla_breached = models.BooleanField(default=False, db_index=True)
    sla_alerted_at = models.DateTimeField(null=True, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    history = HistoricalRecords()

    class Meta:
        ordering = ("-created_at",)
        verbose_name = "chamado"
        verbose_name_plural = "chamados"
        indexes = [
            models.Index(fields=["status", "sla_due_at"]),
            models.Index(fields=["origin", "created_at"]),
            models.Index(fields=["status", "priority", "created_at"]),
        ]

    def __str__(self) -> str:
        return f"{self.code} — {self.title}"

    @classmethod
    def next_code(cls) -> str:
        return f"CH-{timezone.now():%y%m%d}-{uuid.uuid4().hex[:5].upper()}"

    @property
    def is_sla_overdue(self) -> bool:
        if self.status in {self.Status.RESOLVED, self.Status.CLOSED}:
            return False
        return timezone.now() > self.sla_due_at


class TicketEvent(models.Model):
    ticket = models.ForeignKey(Ticket, on_delete=models.CASCADE, related_name="events")
    author = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        null=True,
        blank=True,
        on_delete=models.SET_NULL,
    )
    note = models.TextField()
    status_from = models.CharField(max_length=32, blank=True)
    status_to = models.CharField(max_length=32, blank=True)
    is_internal = models.BooleanField(default=False)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ("created_at",)
        verbose_name = "evento de chamado"
        verbose_name_plural = "eventos de chamado"

    def __str__(self) -> str:
        return f"Event #{self.pk} on {self.ticket_id}"


def ticket_attachment_path(instance: TicketAttachment, filename: str) -> str:
    return f"tickets/{instance.ticket_id}/{filename.replace(' ', '_')}"


class TicketAttachment(models.Model):
    ticket = models.ForeignKey(Ticket, on_delete=models.CASCADE, related_name="attachments")
    file = models.FileField(upload_to=ticket_attachment_path)
    original_name = models.CharField(max_length=255)
    uploaded_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        null=True,
        blank=True,
        on_delete=models.SET_NULL,
    )
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ("-created_at",)

    def __str__(self) -> str:
        return self.original_name


class CrossSellAttribution(models.Model):
    """Tracking simples de pedidos influenciados por cross-sell (F7)."""

    class Source(models.TextChoices):
        PDP = "pdp", "PDP"
        EMAIL = "email", "E-mail pós-compra"
        CHECKER = "checker", "Verificador"

    order = models.ForeignKey(
        "orders.Order",
        on_delete=models.CASCADE,
        related_name="cross_sell_attributions",
    )
    product = models.ForeignKey(
        "products.Product",
        on_delete=models.CASCADE,
        related_name="cross_sell_wins",
    )
    source_product = models.ForeignKey(
        "products.Product",
        null=True,
        blank=True,
        on_delete=models.SET_NULL,
        related_name="cross_sell_sources",
    )
    source = models.CharField(max_length=16, choices=Source.choices, default=Source.PDP)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ("-created_at",)
        verbose_name = "atribuição cross-sell"
        verbose_name_plural = "atribuições cross-sell"
        indexes = [
            models.Index(fields=["source", "created_at"]),
        ]

    def __str__(self) -> str:
        return f"XS {self.product_id} ← {self.source}"
