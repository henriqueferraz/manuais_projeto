"""Carrinho de sessão + itens (F4a)."""

from __future__ import annotations

import uuid

from django.conf import settings
from django.db import models
from django.utils import timezone


class Cart(models.Model):
    """Carrinho anônimo (session_key) ou autenticado."""

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    user = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        null=True,
        blank=True,
        on_delete=models.CASCADE,
        related_name="carts",
    )
    session_key = models.CharField(max_length=64, blank=True, db_index=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ("-updated_at",)
        verbose_name = "carrinho"
        verbose_name_plural = "carrinhos"

    def __str__(self) -> str:
        return f"Cart {self.id}"

    @property
    def item_count(self) -> int:
        return sum(item.quantity for item in self.items.all())

    @property
    def subtotal(self):
        from decimal import Decimal

        total = Decimal("0")
        for item in self.items.select_related("product"):
            total += item.line_total
        return total


class CartItem(models.Model):
    cart = models.ForeignKey(Cart, on_delete=models.CASCADE, related_name="items")
    product = models.ForeignKey(
        "products.Product",
        on_delete=models.CASCADE,
        related_name="cart_items",
    )
    quantity = models.PositiveIntegerField(default=1)
    unit_price = models.DecimalField(max_digits=12, decimal_places=2)
    reserved = models.BooleanField(
        default=False,
        help_text="True quando estoque foi reservado (pré-checkout).",
    )
    reservation_expires_at = models.DateTimeField(null=True, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        unique_together = ("cart", "product")
        verbose_name = "item do carrinho"
        verbose_name_plural = "itens do carrinho"

    def __str__(self) -> str:
        return f"{self.product.sku} x{self.quantity}"

    @property
    def line_total(self):
        return self.unit_price * self.quantity

    @property
    def reservation_active(self) -> bool:
        if not self.reserved or not self.reservation_expires_at:
            return False
        return self.reservation_expires_at > timezone.now()
