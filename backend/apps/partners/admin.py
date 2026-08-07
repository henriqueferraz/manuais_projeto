from django.contrib import admin

from apps.partners.models import PartnerService


@admin.register(PartnerService)
class PartnerServiceAdmin(admin.ModelAdmin):
    list_display = ("name", "city", "state", "active", "phone")
    list_filter = ("state", "active")
    search_fields = ("name", "city", "brands")
