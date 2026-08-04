from django.contrib import admin
from simple_history.admin import SimpleHistoryAdmin

from apps.products.models import Product, ProductTranslation


class ProductTranslationInline(admin.TabularInline):
    model = ProductTranslation
    extra = 1


@admin.register(Product)
class ProductAdmin(SimpleHistoryAdmin):
    list_display = ("sku", "brand", "model_code", "status", "product_kind", "price", "updated_at")
    list_filter = ("status", "product_kind", "brand")
    search_fields = ("sku", "brand", "model_code")
    inlines = [ProductTranslationInline]
    readonly_fields = ("published_at", "created_at", "updated_at")
