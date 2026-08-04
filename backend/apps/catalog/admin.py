from django.contrib import admin
from simple_history.admin import SimpleHistoryAdmin

from apps.catalog.models import Category


@admin.register(Category)
class CategoryAdmin(SimpleHistoryAdmin):
    list_display = ("name", "slug", "parent", "updated_at")
    search_fields = ("name", "slug")
    prepopulated_fields = {"slug": ("name",)}
