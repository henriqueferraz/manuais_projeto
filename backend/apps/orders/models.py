"""Pedidos, itens, pagamento e NF-e (F4b)."""

from __future__ import annotations

import uuid

from django.conf import settings
from django.db import models
from django.utils import timezone
from simple_history.models import HistoricalRecords


class Order(models.Model):
    class Status(models.TextChoices):
        DRAFT = "draft", "Rascunho"
        AWAITING_PAYMENT = "awaiting_payment", "Aguardando pagamento"
        PAID = "paid", "Pago"
        PAYMENT_FAILED = "payment_failed", "Pagamento falhou"
        CANCELLED = "cancelled", "Cancelado"
        FULFILLED = "fulfilled", "Enviado"
        REFUNDED = "refunded", "Estornado"

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    number = models.CharField(max_length=24, unique=True, db_index=True)
    user = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        null=True,
        blank=True,
        on_delete=models.SET_NULL,
        related_name="orders",
    )
    email = models.EmailField()
    status = models.CharField(
        max_length=32,
        choices=Status.choices,
        default=Status.DRAFT,
        db_index=True,
    )
    # Endereço (snapshot)
    shipping_name = models.CharField(max_length=180)
    shipping_phone = models.CharField(max_length=32, blank=True)
    shipping_cep = models.CharField(max_length=9)
    shipping_street = models.CharField(max_length=180)
    shipping_number = models.CharField(max_length=32)
    shipping_complement = models.CharField(max_length=120, blank=True)
    shipping_district = models.CharField(max_length=120)
    shipping_city = models.CharField(max_length=120)
    shipping_state = models.CharField(max_length=2)

    shipping_method = models.CharField(max_length=64, blank=True)
    shipping_carrier = models.CharField(max_length=64, blank=True)
    shipping_quote_id = models.CharField(max_length=128, blank=True)
    shipping_cost = models.DecimalField(max_digits=12, decimal_places=2, default=0)
    shipping_eta_days = models.PositiveSmallIntegerField(null=True, blank=True)

    subtotal = models.DecimalField(max_digits=12, decimal_places=2, default=0)
    discount = models.DecimalField(max_digits=12, decimal_places=2, default=0)
    coupon_code = models.CharField(max_length=40, blank=True)
    total = models.DecimalField(max_digits=12, decimal_places=2, default=0)
    currency = models.CharField(max_length=3, default="BRL")

    cart = models.ForeignKey(
        "cart.Cart",
        null=True,
        blank=True,
        on_delete=models.SET_NULL,
        related_name="orders",
    )
    notes = models.TextField(blank=True)
    paid_at = models.DateTimeField(null=True, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    history = HistoricalRecords()

    class Meta:
        ordering = ("-created_at",)
        verbose_name = "pedido"
        verbose_name_plural = "pedidos"

    def __str__(self) -> str:
        return f"Pedido {self.number}"

    @classmethod
    def next_number(cls) -> str:
        stamp = timezone.now().strftime("%Y%m%d")
        suffix = uuid.uuid4().hex[:6].upper()
        return f"TP-{stamp}-{suffix}"


class OrderItem(models.Model):
    order = models.ForeignKey(Order, on_delete=models.CASCADE, related_name="items")
    product = models.ForeignKey(
        "products.Product",
        null=True,
        blank=True,
        on_delete=models.SET_NULL,
        related_name="order_items",
    )
    sku = models.CharField(max_length=64)
    name = models.CharField(max_length=255)
    quantity = models.PositiveIntegerField()
    unit_price = models.DecimalField(max_digits=12, decimal_places=2)
    line_total = models.DecimalField(max_digits=12, decimal_places=2)

    class Meta:
        verbose_name = "item do pedido"
        verbose_name_plural = "itens do pedido"

    def __str__(self) -> str:
        return f"{self.sku} x{self.quantity}"


class Payment(models.Model):
    """Pagamento tokenizado — NUNCA armazena PAN/CVV."""

    class Status(models.TextChoices):
        PENDING = "pending", "Pendente"
        AUTHORIZED = "authorized", "Autorizado"
        PAID = "paid", "Pago"
        FAILED = "failed", "Falhou"
        REFUNDED = "refunded", "Estornado"
        CANCELLED = "cancelled", "Cancelado"

    class Provider(models.TextChoices):
        MOCK = "mock", "Mock (dev/CI)"
        STRIPE = "stripe", "Stripe"
        MERCADOPAGO = "mercadopago", "Mercado Pago"

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    order = models.ForeignKey(Order, on_delete=models.CASCADE, related_name="payments")
    provider = models.CharField(max_length=32, choices=Provider.choices)
    status = models.CharField(
        max_length=32,
        choices=Status.choices,
        default=Status.PENDING,
        db_index=True,
    )
    amount = models.DecimalField(max_digits=12, decimal_places=2)
    currency = models.CharField(max_length=3, default="BRL")
    # Token / IDs do gateway — nunca cartão em claro
    payment_token = models.CharField(max_length=255, blank=True)
    provider_payment_id = models.CharField(max_length=255, blank=True, db_index=True)
    provider_intent_id = models.CharField(max_length=255, blank=True)
    last4 = models.CharField(max_length=4, blank=True)
    brand = models.CharField(max_length=32, blank=True)
    failure_code = models.CharField(max_length=64, blank=True)
    failure_message = models.CharField(max_length=255, blank=True)
    raw_webhook = models.JSONField(default=dict, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    history = HistoricalRecords()

    class Meta:
        ordering = ("-created_at",)
        verbose_name = "pagamento"
        verbose_name_plural = "pagamentos"

    def __str__(self) -> str:
        return f"Payment {self.pk} [{self.status}]"


class Invoice(models.Model):
    """NF-e emitida via provedor fiscal."""

    class Status(models.TextChoices):
        PENDING = "pending", "Pendente"
        PROCESSING = "processing", "Processando"
        ISSUED = "issued", "Emitida"
        FAILED = "failed", "Falhou"
        CANCELLED = "cancelled", "Cancelada"

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    order = models.OneToOneField(Order, on_delete=models.CASCADE, related_name="invoice")
    status = models.CharField(
        max_length=32,
        choices=Status.choices,
        default=Status.PENDING,
        db_index=True,
    )
    provider = models.CharField(max_length=64, default="mock_fiscal")
    access_key = models.CharField(max_length=44, blank=True)
    number = models.CharField(max_length=20, blank=True)
    series = models.CharField(max_length=5, blank=True)
    pdf_url = models.URLField(blank=True)
    xml_url = models.URLField(blank=True)
    error_message = models.TextField(blank=True)
    attempts = models.PositiveSmallIntegerField(default=0)
    issued_at = models.DateTimeField(null=True, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    history = HistoricalRecords()

    class Meta:
        verbose_name = "NF-e"
        verbose_name_plural = "NF-e"

    def __str__(self) -> str:
        return f"NF-e {self.number or self.pk} [{self.status}]"


class ReturnRequest(models.Model):
    class Status(models.TextChoices):
        REQUESTED = "requested", "Solicitado"
        UNDER_REVIEW = "under_review", "Em análise"
        APPROVED = "approved", "Aprovado"
        REJECTED = "rejected", "Recusado"
        REFUNDED = "refunded", "Reembolsado"
        EXCHANGED = "exchanged", "Trocado"
        CANCELLED = "cancelled", "Cancelado"

    class Kind(models.TextChoices):
        REFUND = "refund", "Reembolso (arrependimento)"
        EXCHANGE = "exchange", "Troca por outra peça"

    class Reason(models.TextChoices):
        REGRET = "regret", "Arrependimento (CDC)"
        DEFECT = "defect", "Defeito"
        WRONG_ITEM = "wrong_item", "Item errado"
        OTHER = "other", "Outro"

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    order = models.ForeignKey(Order, on_delete=models.CASCADE, related_name="return_requests")
    user = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        null=True,
        blank=True,
        on_delete=models.SET_NULL,
        related_name="return_requests",
    )
    email = models.EmailField()
    kind = models.CharField(max_length=16, choices=Kind.choices, default=Kind.REFUND)
    reason = models.CharField(max_length=32, choices=Reason.choices, default=Reason.REGRET)
    details = models.TextField(blank=True)
    status = models.CharField(
        max_length=32,
        choices=Status.choices,
        default=Status.REQUESTED,
        db_index=True,
    )
    delivered_at = models.DateTimeField()
    deadline_at = models.DateTimeField()
    refund_payment_id = models.CharField(max_length=64, blank=True)
    staff_notes = models.TextField(blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    history = HistoricalRecords()

    class Meta:
        ordering = ("-created_at",)
        verbose_name = "solicitação de troca/devolução"
        verbose_name_plural = "solicitações de troca/devolução"

    def __str__(self) -> str:
        return f"Return {self.order.number} [{self.status}]"

    @staticmethod
    def compute_deadline(delivered_at):
        from datetime import timedelta

        days = int(getattr(settings, "RETURN_CDC_DAYS", 7))
        return delivered_at + timedelta(days=days)

    @property
    def within_cdc_window(self) -> bool:
        return timezone.now() <= self.deadline_at
