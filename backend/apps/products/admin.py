from django.contrib import admin
from simple_history.admin import SimpleHistoryAdmin

from apps.products.models import Product, ProductImage, ProductTranslation, Stock


class ProductTranslationInline(admin.TabularInline):
    model = ProductTranslation
    extra = 1


class ProductImageInline(admin.TabularInline):
    model = ProductImage
    extra = 1


class StockInline(admin.StackedInline):
    model = Stock
    extra = 0
    max_num = 1


@admin.register(Product)
class ProductAdmin(SimpleHistoryAdmin):
    list_display = ("sku", "brand", "model_code", "status", "product_kind", "price", "updated_at")
    list_filter = ("status", "product_kind", "brand", "voltage")
    search_fields = ("sku", "brand", "model_code")
    inlines = [ProductTranslationInline, ProductImageInline, StockInline]
    readonly_fields = ("published_at", "created_at", "updated_at")


@admin.register(Stock)
class StockAdmin(SimpleHistoryAdmin):
    list_display = (
        "product",
        "quantity_available",
        "quantity_reserved",
        "minimum_alert",
        "updated_at",
    )
    search_fields = ("product__sku",)
