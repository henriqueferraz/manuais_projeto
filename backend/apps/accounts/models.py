"""Models de auditoria de ações sensíveis."""

from django.conf import settings
from django.db import models
from simple_history.models import HistoricalRecords


class SensitiveActionLog(models.Model):
    """Trilha de auditoria para ações sensíveis (P05/P15)."""

    class Action(models.TextChoices):
        LOGIN = "login", "Login"
        LOGOUT = "logout", "Logout"
        LOGIN_FAILED = "login_failed", "Login falhou"
        PERMISSION_CHANGE = "permission_change", "Alteração de permissão"
        STAFF_ACCESS = "staff_access", "Acesso staff"
        DATA_EXPORT = "data_export", "Exportação de dados"
        OTHER = "other", "Outro"

    action = models.CharField(max_length=64, choices=Action.choices)
    actor = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        null=True,
        blank=True,
        on_delete=models.SET_NULL,
        related_name="sensitive_actions",
    )
    object_repr = models.CharField(max_length=255, blank=True)
    details = models.JSONField(default=dict, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    history = HistoricalRecords()

    class Meta:
        ordering = ("-created_at",)
        verbose_name = "log de ação sensível"
        verbose_name_plural = "logs de ações sensíveis"

    def __str__(self) -> str:
        return f"{self.action} @ {self.created_at:%Y-%m-%d %H:%M}"
