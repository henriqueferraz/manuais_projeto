"""Aplicação de cupons e preço promocional."""

from __future__ import annotations

from decimal import Decimal

from django.core.exceptions import ValidationError
from django.utils import timezone

from apps.cart.models import Coupon, ProductPromotion
from apps.products.models import Product

COUPON_SESSION_KEY = "coupon_code"


def effective_price(product: Product) -> Decimal:
    now = timezone.now()
    promo = (
        ProductPromotion.objects.filter(active=True, valid_from__lte=now, valid_until__gte=now)
        .filter(models_q(product))
        .order_by("promo_price")
        .first()
    )
    if promo:
        return promo.promo_price
    return product.price


def models_q(product: Product):
    from django.db.models import Q

    return Q(product=product) | Q(category=product.category)


def apply_coupon_code(code: str, *, subtotal: Decimal) -> tuple[Coupon, Decimal]:
    code = (code or "").strip().upper()
    if not code:
        raise ValidationError("Informe um cupom.")
    coupon = Coupon.objects.filter(code__iexact=code).first()
    if coupon is None:
        raise ValidationError("Cupom inválido.")
    discount = coupon.discount_for(subtotal)
    return coupon, discount


def cart_totals_with_coupon(cart, coupon_code: str | None = None) -> dict:
    from apps.cart.services import cart_totals

    base = cart_totals(cart)
    discount = Decimal("0")
    coupon = None
    if coupon_code:
        try:
            coupon, discount = apply_coupon_code(coupon_code, subtotal=base["subtotal"])
        except ValidationError:
            raise
    return {
        **base,
        "discount": discount,
        "coupon": coupon,
        "total_after_discount": max(Decimal("0"), base["subtotal"] - discount),
    }
