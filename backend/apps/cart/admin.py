from django.contrib import admin

from apps.cart.models import Cart, CartItem, Coupon, ProductPromotion


class CartItemInline(admin.TabularInline):
    model = CartItem
    extra = 0


@admin.register(Cart)
class CartAdmin(admin.ModelAdmin):
    list_display = ("id", "user", "session_key", "updated_at")
    inlines = [CartItemInline]


@admin.register(Coupon)
class CouponAdmin(admin.ModelAdmin):
    list_display = (
        "code",
        "kind",
        "value",
        "min_subtotal",
        "used_count",
        "max_uses",
        "active",
        "valid_until",
    )
    list_filter = ("kind", "active")
    search_fields = ("code",)


@admin.register(ProductPromotion)
class ProductPromotionAdmin(admin.ModelAdmin):
    list_display = (
        "id",
        "product",
        "category",
        "promo_price",
        "valid_from",
        "valid_until",
        "active",
    )
    list_filter = ("active",)
    search_fields = ("product__sku", "category__slug")
