from django.contrib import admin
from simple_history.admin import SimpleHistoryAdmin

from apps.catalog.models import Brand, Category, EquipmentModel


@admin.register(Category)
class CategoryAdmin(SimpleHistoryAdmin):
    list_display = ("name", "slug", "parent", "updated_at")
    search_fields = ("name", "slug")
    prepopulated_fields = {"slug": ("name",)}


@admin.register(Brand)
class BrandAdmin(SimpleHistoryAdmin):
    list_display = ("name", "slug", "updated_at")
    search_fields = ("name", "slug")
    prepopulated_fields = {"slug": ("name",)}


@admin.register(EquipmentModel)
class EquipmentModelAdmin(SimpleHistoryAdmin):
    list_display = ("code", "brand", "name", "updated_at")
    list_filter = ("brand",)
    search_fields = ("code", "brand", "name", "slug")
    prepopulated_fields = {"slug": ("brand", "code")}
