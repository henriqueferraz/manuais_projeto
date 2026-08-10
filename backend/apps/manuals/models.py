"""Models de manuais e logs de extração (F3 / P09 / P11)."""

from __future__ import annotations

import hashlib
import uuid

from django.conf import settings
from django.db import models
from django.utils import timezone
from simple_history.models import HistoricalRecords


def manual_upload_to(instance: Manual, filename: str) -> str:
    """Caminho no storage: manuals/{uuid}/{filename}."""
    safe = filename.replace(" ", "_")
    return f"manuals/{instance.uuid}/{safe}"


class Manual(models.Model):
    """PDF fonte versionado (R2 ou filesystem local)."""

    class ScanStatus(models.TextChoices):
        PENDING = "pending", "Pendente"
        CLEAN = "clean", "Limpo"
        INFECTED = "infected", "Infectado"
        SKIPPED = "skipped", "Ignorado (dev)"

    uuid = models.UUIDField(default=uuid.uuid4, editable=False, unique=True)
    file = models.FileField(upload_to=manual_upload_to, max_length=512)
    original_filename = models.CharField(max_length=255)
    sha256 = models.CharField(max_length=64, db_index=True, blank=True)
    mime_type = models.CharField(max_length=100, default="application/pdf")
    size_bytes = models.PositiveBigIntegerField(default=0)
    manufacturer = models.CharField(max_length=120, blank=True)
    source_locale = models.CharField(max_length=10, default="pt-BR")
    version = models.PositiveIntegerField(default=1)
    scan_status = models.CharField(
        max_length=16,
        choices=ScanStatus.choices,
        default=ScanStatus.PENDING,
    )
    uploaded_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        null=True,
        blank=True,
        on_delete=models.SET_NULL,
        related_name="uploaded_manuals",
    )
    linked_product = models.ForeignKey(
        "products.Product",
        null=True,
        blank=True,
        on_delete=models.SET_NULL,
        related_name="source_manuals",
    )
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    history = HistoricalRecords()

    class Meta:
        ordering = ("-created_at",)
        verbose_name = "manual"
        verbose_name_plural = "manuais"

    def __str__(self) -> str:
        return self.original_filename

    @property
    def storage_key(self) -> str:
        """Chave/caminho no backend de storage (R2 key)."""
        return self.file.name if self.file else ""

    def compute_and_set_sha256(self, content: bytes) -> str:
        digest = hashlib.sha256(content).hexdigest()
        self.sha256 = digest
        self.size_bytes = len(content)
        return digest


class ExtractionLog(models.Model):
    """Execução do pipeline PDF → JSON estruturado (+ HITL)."""

    class Status(models.TextChoices):
        PENDING = "pending", "Pendente"
        RUNNING = "running", "Em execução"
        AWAITING_REVIEW = "awaiting_review", "Aguardando revisão"
        APPROVED = "approved", "Aprovado"
        REJECTED = "rejected", "Rejeitado"
        FAILED = "failed", "Falhou"

    manual = models.ForeignKey(
        Manual,
        on_delete=models.CASCADE,
        related_name="extractions",
    )
    status = models.CharField(
        max_length=32,
        choices=Status.choices,
        default=Status.PENDING,
        db_index=True,
    )
    prompt_version = models.CharField(max_length=32, default="v3")
    raw_text_preview = models.TextField(blank=True)
    raw_json = models.JSONField(default=dict, blank=True)
    corrected_json = models.JSONField(default=dict, blank=True)
    model_name = models.CharField(max_length=120, blank=True)
    tokens_in = models.PositiveIntegerField(default=0)
    tokens_out = models.PositiveIntegerField(default=0)
    cost_estimate = models.DecimalField(max_digits=10, decimal_places=6, default=0)
    confidence = models.FloatField(null=True, blank=True)
    error_message = models.TextField(blank=True)
    langsmith_trace_id = models.CharField(max_length=128, blank=True)
    draft_product = models.ForeignKey(
        "products.Product",
        null=True,
        blank=True,
        on_delete=models.SET_NULL,
        related_name="extraction_logs",
    )
    reviewed_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        null=True,
        blank=True,
        on_delete=models.SET_NULL,
        related_name="reviewed_extractions",
    )
    reviewed_at = models.DateTimeField(null=True, blank=True)
    review_notes = models.TextField(blank=True)
    langgraph_thread_id = models.CharField(
        max_length=64,
        blank=True,
        db_index=True,
        help_text="Thread LangGraph para pausa/retomada HITL (F6).",
    )
    langgraph_interrupted = models.BooleanField(
        default=False,
        help_text="True quando o grafo pausou aguardando revisão humana.",
    )
    started_at = models.DateTimeField(null=True, blank=True)
    finished_at = models.DateTimeField(null=True, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    history = HistoricalRecords()

    class Meta:
        ordering = ("-created_at",)
        verbose_name = "log de extração"
        verbose_name_plural = "logs de extração"

    def __str__(self) -> str:
        return f"Extraction #{self.pk} [{self.status}] — {self.manual}"

    def mark_running(self) -> None:
        self.status = self.Status.RUNNING
        self.started_at = timezone.now()
        self.save(update_fields=["status", "started_at", "updated_at"])

    def mark_failed(self, message: str) -> None:
        self.status = self.Status.FAILED
        self.error_message = message[:4000]
        self.finished_at = timezone.now()
        self.save(update_fields=["status", "error_message", "finished_at", "updated_at"])
