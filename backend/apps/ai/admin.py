from django.contrib import admin

from apps.ai.models import ChatFeedback, ChatMessage, ChatSession, ManualChunk, PhotoSearch


@admin.register(ManualChunk)
class ManualChunkAdmin(admin.ModelAdmin):
    list_display = ("id", "manual", "product", "section", "page", "chunk_index", "indexed_at")
    list_filter = ("category",)
    search_fields = ("content", "section", "manual__original_filename")
    raw_id_fields = ("manual", "product", "category")


class ChatMessageInline(admin.TabularInline):
    model = ChatMessage
    extra = 0
    readonly_fields = (
        "role",
        "content",
        "sources",
        "confidence",
        "found_in_manual",
        "diagnosis_card",
        "cost_estimate",
        "latency_ms",
        "created_at",
    )


@admin.register(ChatSession)
class ChatSessionAdmin(admin.ModelAdmin):
    list_display = (
        "id",
        "title",
        "user",
        "product",
        "consecutive_downvotes",
        "escalated_ticket",
        "updated_at",
    )
    search_fields = ("title", "anonymous_key", "request_id")
    raw_id_fields = ("user", "product", "category", "escalated_ticket")
    inlines = [ChatMessageInline]


@admin.register(ChatFeedback)
class ChatFeedbackAdmin(admin.ModelAdmin):
    list_display = ("id", "message", "vote", "created_ticket", "created_at")
    list_filter = ("vote",)
    raw_id_fields = ("message", "created_ticket")


@admin.register(PhotoSearch)
class PhotoSearchAdmin(admin.ModelAdmin):
    list_display = (
        "id",
        "status",
        "original_filename",
        "user",
        "latency_ms",
        "created_at",
    )
    list_filter = ("status",)
    raw_id_fields = ("user", "product")
