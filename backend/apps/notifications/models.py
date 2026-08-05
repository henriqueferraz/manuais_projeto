"""Log de e-mails transacionais e bounces."""

from django.db import models


class EmailLog(models.Model):
    class Kind(models.TextChoices):
        ORDER_CONFIRMATION = "order_confirmation", "Confirmação de pedido"
        INVOICE = "invoice", "NF-e"
        OTHER = "other", "Outro"

    class Status(models.TextChoices):
        QUEUED = "queued", "Na fila"
        SENT = "sent", "Enviado"
        FAILED = "failed", "Falhou"
        BOUNCED = "bounced", "Bounce"

    to_email = models.EmailField()
    subject = models.CharField(max_length=255)
    kind = models.CharField(max_length=32, choices=Kind.choices, default=Kind.OTHER)
    status = models.CharField(
        max_length=16,
        choices=Status.choices,
        default=Status.QUEUED,
        db_index=True,
    )
    order = models.ForeignKey(
        "orders.Order",
        null=True,
        blank=True,
        on_delete=models.SET_NULL,
        related_name="emails",
    )
    provider_message_id = models.CharField(max_length=255, blank=True)
    error_message = models.TextField(blank=True)
    bounce_detail = models.TextField(blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ("-created_at",)
        verbose_name = "log de e-mail"
        verbose_name_plural = "logs de e-mail"

    def __str__(self) -> str:
        return f"{self.kind} → {self.to_email} [{self.status}]"
