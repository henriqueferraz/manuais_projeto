"""Models de RAG / chat de suporte (F5)."""

from __future__ import annotations

import uuid

from django.conf import settings
from django.db import models


class ManualChunk(models.Model):
    """Trecho indexado de um manual para retrieval semântico."""

    manual = models.ForeignKey(
        "manuals.Manual",
        on_delete=models.CASCADE,
        related_name="chunks",
    )
    product = models.ForeignKey(
        "products.Product",
        null=True,
        blank=True,
        on_delete=models.SET_NULL,
        related_name="manual_chunks",
    )
    category = models.ForeignKey(
        "catalog.Category",
        null=True,
        blank=True,
        on_delete=models.SET_NULL,
        related_name="manual_chunks",
    )
    content = models.TextField()
    section = models.CharField(max_length=255, blank=True, db_index=True)
    page = models.PositiveIntegerField(null=True, blank=True)
    chunk_index = models.PositiveIntegerField(default=0)
    embedding = models.JSONField(default=list, blank=True)
    embedding_dims = models.PositiveIntegerField(default=0)
    metadata = models.JSONField(default=dict, blank=True)
    indexed_at = models.DateTimeField(auto_now=True)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ("manual_id", "chunk_index")
        indexes = [
            models.Index(fields=["manual", "chunk_index"]),
            models.Index(fields=["product", "category"]),
        ]
        verbose_name = "chunk de manual"
        verbose_name_plural = "chunks de manuais"

    def __str__(self) -> str:
        section = self.section or f"chunk-{self.chunk_index}"
        return f"{self.manual_id}:{section}"


class ChatSession(models.Model):
    """Conversa de suporte técnico via RAG."""

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    user = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        null=True,
        blank=True,
        on_delete=models.SET_NULL,
        related_name="chat_sessions",
    )
    anonymous_key = models.CharField(max_length=64, blank=True, db_index=True)
    product = models.ForeignKey(
        "products.Product",
        null=True,
        blank=True,
        on_delete=models.SET_NULL,
        related_name="chat_sessions",
    )
    category = models.ForeignKey(
        "catalog.Category",
        null=True,
        blank=True,
        on_delete=models.SET_NULL,
        related_name="chat_sessions",
    )
    title = models.CharField(max_length=200, blank=True)
    request_id = models.CharField(max_length=64, blank=True)
    langsmith_trace_id = models.CharField(max_length=128, blank=True)
    consecutive_downvotes = models.PositiveSmallIntegerField(default=0)
    escalated_ticket = models.ForeignKey(
        "tickets.Ticket",
        null=True,
        blank=True,
        on_delete=models.SET_NULL,
        related_name="chat_sessions",
    )
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ("-updated_at",)
        verbose_name = "sessão de chat"
        verbose_name_plural = "sessões de chat"

    def __str__(self) -> str:
        return self.title or f"Chat {self.pk}"


class ChatMessage(models.Model):
    class Role(models.TextChoices):
        USER = "user", "Usuário"
        ASSISTANT = "assistant", "Assistente"
        SYSTEM = "system", "Sistema"

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    session = models.ForeignKey(
        ChatSession,
        on_delete=models.CASCADE,
        related_name="messages",
    )
    role = models.CharField(max_length=16, choices=Role.choices)
    content = models.TextField()
    sources = models.JSONField(default=list, blank=True)
    chunk_ids = models.JSONField(default=list, blank=True)
    confidence = models.FloatField(null=True, blank=True)
    found_in_manual = models.BooleanField(default=True)
    tokens_in = models.PositiveIntegerField(default=0)
    tokens_out = models.PositiveIntegerField(default=0)
    cost_estimate = models.DecimalField(max_digits=10, decimal_places=6, default=0)
    latency_ms = models.PositiveIntegerField(default=0)
    langsmith_trace_id = models.CharField(max_length=128, blank=True)
    model_name = models.CharField(max_length=120, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ("created_at",)
        verbose_name = "mensagem de chat"
        verbose_name_plural = "mensagens de chat"

    def __str__(self) -> str:
        return f"{self.role}: {self.content[:60]}"


class ChatFeedback(models.Model):
    class Vote(models.TextChoices):
        UP = "up", "Útil"
        DOWN = "down", "Não útil"

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    message = models.OneToOneField(
        ChatMessage,
        on_delete=models.CASCADE,
        related_name="feedback",
    )
    vote = models.CharField(max_length=8, choices=Vote.choices)
    reason = models.TextField(blank=True)
    chunk_ids_snapshot = models.JSONField(default=list, blank=True)
    created_ticket = models.ForeignKey(
        "tickets.Ticket",
        null=True,
        blank=True,
        on_delete=models.SET_NULL,
        related_name="chat_feedbacks",
    )
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        verbose_name = "feedback de chat"
        verbose_name_plural = "feedbacks de chat"

    def __str__(self) -> str:
        return f"{self.vote} em {self.message_id}"
