"""Sinais de auditoria para ações sensíveis de conta."""

from __future__ import annotations

import structlog
from django.contrib.auth.signals import user_logged_in, user_logged_out, user_login_failed
from django.dispatch import receiver

logger = structlog.get_logger(__name__)


@receiver(user_logged_in)
def audit_login(sender, request, user, **kwargs):
    from apps.accounts.models import SensitiveActionLog

    SensitiveActionLog.objects.create(
        action=SensitiveActionLog.Action.LOGIN,
        actor=user,
        object_repr=user.get_username(),
        details={"path": getattr(request, "path", "")},
    )
    logger.info("auth.login", user_id=user.pk, username=user.get_username())


@receiver(user_logged_out)
def audit_logout(sender, request, user, **kwargs):
    from apps.accounts.models import SensitiveActionLog

    if user and getattr(user, "is_authenticated", False):
        SensitiveActionLog.objects.create(
            action=SensitiveActionLog.Action.LOGOUT,
            actor=user,
            object_repr=user.get_username(),
        )
    logger.info(
        "auth.logout",
        user_id=getattr(user, "pk", None),
        username=getattr(user, "get_username", lambda: None)(),
    )


@receiver(user_login_failed)
def audit_login_failed(sender, credentials, request, **kwargs):
    from apps.accounts.models import SensitiveActionLog

    username = credentials.get("username", "[unknown]")
    SensitiveActionLog.objects.create(
        action=SensitiveActionLog.Action.LOGIN_FAILED,
        object_repr=str(username),
        details={"ip": getattr(request, "META", {}).get("REMOTE_ADDR")},
    )
    logger.warning("auth.login_failed", username=username)
