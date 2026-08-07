"""Assistências técnicas parceiras (F8 / ADR-0005)."""

from __future__ import annotations

from django.db import models


class PartnerService(models.Model):
    name = models.CharField(max_length=180)
    legal_name = models.CharField(max_length=180, blank=True)
    email = models.EmailField(blank=True)
    phone = models.CharField(max_length=32, blank=True)
    city = models.CharField(max_length=120, db_index=True)
    state = models.CharField(max_length=2, db_index=True)
    cep = models.CharField(max_length=9, blank=True)
    address = models.CharField(max_length=255, blank=True)
    latitude = models.DecimalField(max_digits=9, decimal_places=6, null=True, blank=True)
    longitude = models.DecimalField(max_digits=9, decimal_places=6, null=True, blank=True)
    brands = models.CharField(
        max_length=255, blank=True, help_text="Marcas atendidas, separadas por vírgula"
    )
    active = models.BooleanField(default=True, db_index=True)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ("state", "city", "name")
        verbose_name = "assistência parceira"
        verbose_name_plural = "assistências parceiras"
        indexes = [
            models.Index(fields=["state", "city", "active"]),
        ]

    def __str__(self) -> str:
        return f"{self.name} — {self.city}/{self.state}"
