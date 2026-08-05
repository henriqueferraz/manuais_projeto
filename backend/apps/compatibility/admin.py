from django.contrib import admin
from simple_history.admin import SimpleHistoryAdmin

from apps.compatibility.models import Compatibility


@admin.register(Compatibility)
class CompatibilityAdmin(SimpleHistoryAdmin):
    list_display = ("equipment_brand", "equipment_model", "part_product", "updated_at")
    list_filter = ("equipment_brand",)
    search_fields = ("equipment_brand", "equipment_model", "part_product__sku")
    autocomplete_fields = ("part_product",)
