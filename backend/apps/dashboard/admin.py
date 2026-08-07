from django.contrib import admin

from apps.dashboard.models import OpsAlert


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
