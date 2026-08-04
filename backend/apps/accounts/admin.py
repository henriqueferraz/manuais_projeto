"""Admin de contas — 2FA via TWO_FACTOR_PATCH_ADMIN."""

from django.contrib import admin
from django.contrib.auth.admin import UserAdmin as DjangoUserAdmin
from django.contrib.auth.models import User
from simple_history.admin import SimpleHistoryAdmin

from .models import SensitiveActionLog

if admin.site.is_registered(User):
    admin.site.unregister(User)


@admin.register(User)
class UserAdmin(DjangoUserAdmin):
    list_display = ("username", "email", "is_staff", "is_active", "last_login")


@admin.register(SensitiveActionLog)
class SensitiveActionLogAdmin(SimpleHistoryAdmin):
    list_display = ("action", "actor", "object_repr", "created_at")
    list_filter = ("action", "created_at")
    search_fields = ("object_repr", "actor__username")
    readonly_fields = ("action", "actor", "object_repr", "details", "created_at")
