"""Planos e assinaturas de manutenção (F8 / ADR-0004)."""

from __future__ import annotations

import uuid
from datetime import timedelta

from django.conf import settings
from django.db import models
from django.utils import timezone


class SubscriptionPlan(models.Model):
    code = models.SlugField(max_length=40, unique=True)
    name = models.CharField(max_length=120)
    description = models.TextField(blank=True)
    price_monthly = models.DecimalField(max_digits=12, decimal_places=2)
    currency = models.CharField(max_length=3, default="BRL")
    interval_days = models.PositiveIntegerField(default=30)
    active = models.BooleanField(default=True, db_index=True)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ("price_monthly",)
        verbose_name = "plano de assinatura"
        verbose_name_plural = "planos de assinatura"

    def __str__(self) -> str:
        return self.name


class Subscription(models.Model):
    class Status(models.TextChoices):
        TRIAL = "trial", "Trial"
        ACTIVE = "active", "Ativa"
        PAST_DUE = "past_due", "Em atraso"
        CANCELLED = "cancelled", "Cancelada"

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    plan = models.ForeignKey(
        SubscriptionPlan, on_delete=models.PROTECT, related_name="subscriptions"
    )
    user = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        null=True,
        blank=True,
        on_delete=models.SET_NULL,
        related_name="subscriptions",
    )
    email = models.EmailField()
    status = models.CharField(max_length=16, choices=Status.choices, default=Status.ACTIVE)
    started_at = models.DateTimeField(default=timezone.now)
    current_period_end = models.DateTimeField()
    cancelled_at = models.DateTimeField(null=True, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ("-created_at",)
        verbose_name = "assinatura"
        verbose_name_plural = "assinaturas"

    def __str__(self) -> str:
        return f"{self.email} · {self.plan.code}"

    @classmethod
    def start_mock(cls, *, plan: SubscriptionPlan, email: str, user=None) -> Subscription:
        return cls.objects.create(
            plan=plan,
            email=email,
            user=user if getattr(user, "is_authenticated", False) else None,
            status=cls.Status.ACTIVE,
            current_period_end=timezone.now() + timedelta(days=plan.interval_days),
        )
