from django.contrib import admin
from simple_history.admin import SimpleHistoryAdmin

from apps.tickets.models import CrossSellAttribution, Ticket, TicketAttachment, TicketEvent


class TicketEventInline(admin.TabularInline):
    model = TicketEvent
    extra = 0
    readonly_fields = ("created_at",)


class TicketAttachmentInline(admin.TabularInline):
    model = TicketAttachment
    extra = 0


@admin.register(Ticket)
class TicketAdmin(SimpleHistoryAdmin):
    list_display = (
        "code",
        "title",
        "status",
        "priority",
        "sla_due_at",
        "sla_breached",
        "created_at",
    )
    list_filter = ("status", "priority", "sla_breached", "origin")
    search_fields = ("code", "email", "title", "equipment")
    inlines = [TicketEventInline, TicketAttachmentInline]


@admin.register(CrossSellAttribution)
class CrossSellAttributionAdmin(admin.ModelAdmin):
    list_display = ("order", "product", "source_product", "source", "created_at")
    list_filter = ("source",)
