from django.contrib import admin

from apps.dashboard.models import HomeHeroSlide, OpsAlert


@admin.register(OpsAlert)
class OpsAlertAdmin(admin.ModelAdmin):
    list_display = (
        "title",
        "kind",
        "severity",
        "acknowledged",
        "channel",
        "created_at",
    )
    list_filter = ("severity", "kind", "acknowledged")
    search_fields = ("title", "message")
    raw_id_fields = ("acknowledged_by",)


@admin.register(HomeHeroSlide)
class HomeHeroSlideAdmin(admin.ModelAdmin):
    list_display = ("title", "badge", "sort_order", "is_active", "updated_at")
    list_filter = ("is_active",)
    search_fields = ("title", "badge", "lead")
    list_editable = ("sort_order", "is_active")
    ordering = ("sort_order", "id")
