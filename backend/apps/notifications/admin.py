from django.contrib import admin

from apps.notifications.models import EmailLog


@admin.register(EmailLog)
class EmailLogAdmin(admin.ModelAdmin):
    list_display = ("to_email", "kind", "status", "subject", "created_at")
    list_filter = ("kind", "status")
    search_fields = ("to_email", "subject", "provider_message_id")
    readonly_fields = ("created_at", "updated_at")
