"""Admin + ações HITL para manuais e extrações."""

from django.contrib import admin, messages
from django.utils.html import format_html
from simple_history.admin import SimpleHistoryAdmin

from apps.manuals.models import ExtractionLog, Manual
from apps.manuals.services.pipeline import approve_extraction, reject_extraction
from apps.manuals.storage import signed_url


@admin.register(Manual)
class ManualAdmin(SimpleHistoryAdmin):
    list_display = (
        "original_filename",
        "manufacturer",
        "version",
        "scan_status",
        "size_bytes",
        "created_at",
        "download_link",
    )
    list_filter = ("scan_status", "manufacturer", "source_locale")
    search_fields = ("original_filename", "sha256", "manufacturer")
    readonly_fields = ("uuid", "sha256", "size_bytes", "mime_type", "created_at", "updated_at")

    @admin.display(description="Download")
    def download_link(self, obj: Manual):
        url = signed_url(obj.storage_key)
        if not url:
            return "—"
        return format_html('<a href="{}" target="_blank" rel="noopener">PDF</a>', url)


@admin.register(ExtractionLog)
class ExtractionLogAdmin(SimpleHistoryAdmin):
    list_display = (
        "id",
        "manual",
        "status",
        "confidence",
        "model_name",
        "cost_estimate",
        "reviewed_by",
        "created_at",
    )
    list_filter = ("status", "prompt_version", "model_name")
    search_fields = ("manual__original_filename", "manual__manufacturer")
    readonly_fields = (
        "started_at",
        "finished_at",
        "tokens_in",
        "tokens_out",
        "cost_estimate",
        "langsmith_trace_id",
        "created_at",
        "updated_at",
    )
    actions = ("action_approve", "action_reject")

    @admin.action(description="Aprovar e criar rascunho de produto")
    def action_approve(self, request, queryset):
        ok = 0
        for log in queryset:
            try:
                approve_extraction(log, reviewer=request.user)
                ok += 1
            except Exception as exc:  # noqa: BLE001
                self.message_user(request, f"#{log.pk}: {exc}", level=messages.ERROR)
        self.message_user(request, f"{ok} extração(ões) aprovada(s) como rascunho.")

    @admin.action(description="Rejeitar extração")
    def action_reject(self, request, queryset):
        ok = 0
        for log in queryset:
            try:
                reject_extraction(log, reviewer=request.user, notes="Rejeitado via admin")
                ok += 1
            except Exception as exc:  # noqa: BLE001
                self.message_user(request, f"#{log.pk}: {exc}", level=messages.ERROR)
        self.message_user(request, f"{ok} extração(ões) rejeitada(s).")
