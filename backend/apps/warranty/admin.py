from django.contrib import admin

from apps.warranty.models import WarrantyCode


@admin.register(WarrantyCode)
class WarrantyCodeAdmin(admin.ModelAdmin):
    list_display = ("id", "sku", "label", "active", "created_at")
    list_filter = ("active",)
    raw_id_fields = ("product",)
    search_fields = ("sku", "label")
