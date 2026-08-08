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


class Coupon(models.Model):
    class Kind(models.TextChoices):
        PERCENT = "percent", "Percentual"
        FIXED = "fixed", "Valor fixo"

    code = models.CharField(max_length=40, unique=True, db_index=True)
    kind = models.CharField(max_length=16, choices=Kind.choices, default=Kind.PERCENT)
    value = models.DecimalField(max_digits=10, decimal_places=2)
    min_subtotal = models.DecimalField(max_digits=12, decimal_places=2, default=0)
    max_uses = models.PositiveIntegerField(null=True, blank=True)
    used_count = models.PositiveIntegerField(default=0)
    valid_from = models.DateTimeField(null=True, blank=True)
    valid_until = models.DateTimeField(null=True, blank=True)
    active = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ("code",)
        verbose_name = "cupom"
        verbose_name_plural = "cupons"

    def __str__(self) -> str:
        return self.code

    def is_valid_now(self, *, subtotal):
        from django.core.exceptions import ValidationError

        now = timezone.now()
        if not self.active:
            raise ValidationError("Cupom inativo.")
        if self.valid_from and now < self.valid_from:
            raise ValidationError("Cupom ainda não válido.")
        if self.valid_until and now > self.valid_until:
            raise ValidationError("Cupom expirado.")
        if self.max_uses is not None and self.used_count >= self.max_uses:
            raise ValidationError("Cupom esgotado.")
        if subtotal < self.min_subtotal:
            from apps.core.money import format_brl

            raise ValidationError(
                f"Pedido mínimo de {format_brl(self.min_subtotal)} para este cupom."
            )

    def discount_for(self, subtotal):
        from decimal import Decimal

        self.is_valid_now(subtotal=subtotal)
        if self.kind == self.Kind.PERCENT:
            return (subtotal * self.value / Decimal("100")).quantize(Decimal("0.01"))
        return min(self.value, subtotal)


class ProductPromotion(models.Model):
    product = models.ForeignKey(
        "products.Product",
        null=True,
        blank=True,
        on_delete=models.CASCADE,
        related_name="promotions",
    )
    category = models.ForeignKey(
        "catalog.Category",
        null=True,
        blank=True,
        on_delete=models.CASCADE,
        related_name="promotions",
    )
    promo_price = models.DecimalField(max_digits=12, decimal_places=2)
    valid_from = models.DateTimeField()
    valid_until = models.DateTimeField()
    active = models.BooleanField(default=True)

    class Meta:
        verbose_name = "promoção"
        verbose_name_plural = "promoções"

    def __str__(self) -> str:
        from apps.core.money import format_brl

        return f"Promo → {format_brl(self.promo_price)}"

    def is_current(self) -> bool:
        now = timezone.now()
        return self.active and self.valid_from <= now <= self.valid_until
