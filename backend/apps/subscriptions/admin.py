from django.contrib import admin

from apps.subscriptions.models import Subscription, SubscriptionPlan


@admin.register(SubscriptionPlan)
class SubscriptionPlanAdmin(admin.ModelAdmin):
    list_display = ("code", "name", "price_monthly", "active")
    list_filter = ("active",)


@admin.register(Subscription)
class SubscriptionAdmin(admin.ModelAdmin):
    list_display = ("email", "plan", "status", "current_period_end", "created_at")
    list_filter = ("status",)
    raw_id_fields = ("user", "plan")
