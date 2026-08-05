"""Serviços de estoque e carrinho."""

from __future__ import annotations

from datetime import timedelta
from decimal import Decimal

from django.conf import settings
from django.core.exceptions import ValidationError
from django.db import transaction
from django.utils import timezone

from apps.cart.models import Cart, CartItem
from apps.products.models import Product, Stock

CART_SESSION_KEY = "cart_id"


def reservation_ttl() -> timedelta:
    minutes = int(getattr(settings, "CART_RESERVATION_MINUTES", 30))
    return timedelta(minutes=minutes)


def get_or_create_cart(request) -> Cart:
    cart = None
    cart_id = request.session.get(CART_SESSION_KEY)
    if cart_id:
        cart = Cart.objects.filter(pk=cart_id).first()

    if cart is None and request.user.is_authenticated:
        cart = Cart.objects.filter(user=request.user).order_by("-updated_at").first()

    if cart is None:
        cart = Cart.objects.create(
            user=request.user if request.user.is_authenticated else None,
            session_key=request.session.session_key or "",
        )
        if not request.session.session_key:
            request.session.create()
        cart.session_key = request.session.session_key or ""
        cart.save(update_fields=["session_key", "updated_at"])

    request.session[CART_SESSION_KEY] = str(cart.pk)
    return cart


@transaction.atomic
def add_to_cart(request, product: Product, quantity: int = 1) -> CartItem:
    if product.status != Product.Status.PUBLISHED:
        raise ValidationError("Produto indisponível.")
    if quantity < 1:
        raise ValidationError("Quantidade inválida.")

    cart = get_or_create_cart(request)
    stock = Stock.objects.select_for_update().filter(product=product).first()
    if stock is None or stock.sellable < quantity:
        raise ValidationError("Sem estoque suficiente para este item.")

    item, created = CartItem.objects.select_for_update().get_or_create(
        cart=cart,
        product=product,
        defaults={
            "quantity": quantity,
            "unit_price": product.price,
        },
    )
    if not created:
        new_qty = item.quantity + quantity
        # sellable already counts current reservations; if this item was reserved,
        # its qty is in quantity_reserved — allow increasing within sellable + own reserved
        own = item.quantity if item.reserved else 0
        if stock.sellable + own < new_qty:
            raise ValidationError("Sem estoque suficiente para a quantidade pedida.")
        if item.reserved:
            delta = new_qty - item.quantity
            if delta > 0:
                Stock.reserve(product.id, delta)
            item.quantity = new_qty
            item.reservation_expires_at = timezone.now() + reservation_ttl()
        else:
            item.quantity = new_qty
        item.unit_price = product.price
        item.save()
    else:
        # Reserva imediata ao adicionar (evita overselling)
        Stock.reserve(product.id, quantity)
        item.reserved = True
        item.reservation_expires_at = timezone.now() + reservation_ttl()
        item.save(update_fields=["reserved", "reservation_expires_at", "updated_at"])

    cart.updated_at = timezone.now()
    cart.save(update_fields=["updated_at"])
    return item


@transaction.atomic
def update_cart_item(request, product_id: int, quantity: int) -> CartItem | None:
    cart = get_or_create_cart(request)
    item = (
        CartItem.objects.select_for_update()
        .select_related("product")
        .filter(cart=cart, product_id=product_id)
        .first()
    )
    if item is None:
        return None

    if quantity < 1:
        return remove_cart_item(request, product_id)

    stock = Stock.objects.select_for_update().get(product_id=product_id)
    own = item.quantity if item.reserved else 0
    if stock.sellable + own < quantity:
        raise ValidationError("Sem estoque suficiente.")

    if item.reserved:
        delta = quantity - item.quantity
        if delta > 0:
            Stock.reserve(product_id, delta)
        elif delta < 0:
            Stock.release(product_id, -delta)
        item.reservation_expires_at = timezone.now() + reservation_ttl()

    item.quantity = quantity
    item.unit_price = item.product.price
    item.save()
    return item


@transaction.atomic
def remove_cart_item(request, product_id: int) -> None:
    cart = get_or_create_cart(request)
    item = CartItem.objects.select_for_update().filter(cart=cart, product_id=product_id).first()
    if item is None:
        return
    if item.reserved:
        Stock.release(product_id, item.quantity)
    item.delete()


def cart_totals(cart: Cart) -> dict:
    items = list(cart.items.select_related("product"))
    subtotal = sum((i.line_total for i in items), Decimal("0"))
    return {
        "items": items,
        "count": sum(i.quantity for i in items),
        "subtotal": subtotal,
    }
