from django.contrib import admin
from simple_history.admin import SimpleHistoryAdmin

from apps.orders.models import Invoice, Order, OrderItem, Payment, ReturnRequest


class OrderItemInline(admin.TabularInline):
    model = OrderItem
    extra = 0
    readonly_fields = ("sku", "name", "quantity", "unit_price", "line_total")


class PaymentInline(admin.TabularInline):
    model = Payment
    extra = 0
    readonly_fields = (
        "provider",
        "status",
        "amount",
        "provider_payment_id",
        "last4",
        "brand",
        "failure_code",
    )


@admin.register(Order)
class OrderAdmin(SimpleHistoryAdmin):
    list_display = ("number", "email", "status", "subtotal", "discount", "total", "created_at")
    list_filter = ("status",)
    search_fields = ("number", "email")
    inlines = [OrderItemInline, PaymentInline]
    readonly_fields = ("number", "paid_at", "created_at", "updated_at")


@admin.register(Payment)
class PaymentAdmin(SimpleHistoryAdmin):
    list_display = ("id", "order", "provider", "status", "amount", "last4", "created_at")
    list_filter = ("provider", "status")
    search_fields = ("provider_payment_id", "order__number")
    readonly_fields = ("payment_token", "raw_webhook")


@admin.register(Invoice)
class InvoiceAdmin(SimpleHistoryAdmin):
    list_display = ("order", "status", "number", "series", "attempts", "issued_at")
    list_filter = ("status",)
    actions = ("retry_emit",)

    @admin.action(description="Reprocessar emissão NF-e")
    def retry_emit(self, request, queryset):
        from apps.checkout.tasks import emit_invoice_task

        for inv in queryset:
            emit_invoice_task.delay(str(inv.order_id))
        self.message_user(request, f"{queryset.count()} NF-e reenfileirada(s).")


@admin.register(ReturnRequest)
class ReturnRequestAdmin(SimpleHistoryAdmin):
    list_display = ("order", "email", "kind", "reason", "status", "deadline_at", "created_at")
    list_filter = ("status", "kind", "reason")
    search_fields = ("order__number", "email")
    readonly_fields = ("created_at", "updated_at", "deadline_at")
