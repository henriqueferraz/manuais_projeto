"""Models do dashboard / alertas operacionais (F7) + hero da home."""

from __future__ import annotations

import uuid

from django.conf import settings
from django.db import models


class OpsAlert(models.Model):
    class Severity(models.TextChoices):
        INFO = "info", "Info"
        WARNING = "warning", "Aviso"
        CRITICAL = "critical", "Crítico"

    class Kind(models.TextChoices):
        COST = "cost", "Custo IA"
        SLA = "sla", "SLA"
        ERROR = "error", "Erro recorrente"
        QUEUE = "queue", "Fila"
        INCIDENT = "incident", "Incidente"
        OTHER = "other", "Outro"

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    kind = models.CharField(max_length=16, choices=Kind.choices, default=Kind.OTHER)
    severity = models.CharField(
        max_length=16,
        choices=Severity.choices,
        default=Severity.WARNING,
        db_index=True,
    )
    title = models.CharField(max_length=200)
    message = models.TextField()
    payload = models.JSONField(default=dict, blank=True)
    channel = models.CharField(max_length=64, blank=True, default="panel")
    acknowledged = models.BooleanField(default=False, db_index=True)
    acknowledged_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        null=True,
        blank=True,
        on_delete=models.SET_NULL,
        related_name="acked_ops_alerts",
    )
    acknowledged_at = models.DateTimeField(null=True, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ("-created_at",)
        verbose_name = "alerta operacional"
        verbose_name_plural = "alertas operacionais"

    def __str__(self) -> str:
        return f"[{self.severity}] {self.title}"


def home_hero_image_upload_to(instance: "HomeHeroSlide", filename: str) -> str:
    safe = filename.replace(" ", "_")
    uid = instance.pk or uuid.uuid4()
    return f"branding/hero/{uid}/{safe}"


class HomeHeroSlide(models.Model):
    """Slide do carrossel full-bleed da home (textos + imagem no R2)."""

    badge = models.CharField(
        max_length=64,
        blank=True,
        help_text="Eyebrow opcional (ex.: TECNOLOGIA AI)",
    )
    title = models.CharField(max_length=160)
    lead = models.TextField(blank=True)
    image = models.ImageField(upload_to=home_hero_image_upload_to, blank=True)
    alt_text = models.CharField(max_length=255, blank=True)
    sort_order = models.PositiveIntegerField(default=0, db_index=True)
    is_active = models.BooleanField(default=True, db_index=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ("sort_order", "id")
        verbose_name = "slide do hero"
        verbose_name_plural = "slides do hero"

    def __str__(self) -> str:
        return self.title
