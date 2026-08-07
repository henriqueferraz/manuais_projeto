"""Garantia digital com QR (F8 / ADR-0007)."""

from __future__ import annotations

import io
import uuid

import qrcode
from django.db import models
from django.urls import reverse


class WarrantyCode(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    product = models.ForeignKey(
        "products.Product",
        null=True,
        blank=True,
        on_delete=models.SET_NULL,
        related_name="warranty_codes",
    )
    sku = models.CharField(max_length=64, blank=True, db_index=True)
    label = models.CharField(max_length=120, blank=True)
    active = models.BooleanField(default=True, db_index=True)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ("-created_at",)
        verbose_name = "código de garantia"
        verbose_name_plural = "códigos de garantia"

    def __str__(self) -> str:
        return self.label or str(self.pk)

    def public_path(self) -> str:
        return reverse("warranty:claim", kwargs={"code_id": self.pk})

    def qr_png_bytes(self, absolute_url: str) -> bytes:
        img = qrcode.make(absolute_url)
        buf = io.BytesIO()
        img.save(buf, format="PNG")
        return buf.getvalue()
