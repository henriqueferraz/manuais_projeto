"""Produto, imagens e estoque (F4a / schema F1)."""

from __future__ import annotations

from django.core.exceptions import ValidationError
from django.db import models, transaction
from django.db.models import F
from django.utils import timezone
from django.utils.text import slugify
from simple_history.models import HistoricalRecords


class Product(models.Model):
    class Status(models.TextChoices):
        DRAFT = "draft", "Rascunho"
        PUBLISHED = "published", "Publicado"
        ARCHIVED = "archived", "Arquivado"

    class Kind(models.TextChoices):
        FINISHED_GOOD = "finished_good", "Produto acabado"
        SPARE_PART = "spare_part", "Peça de reposição"

    sku = models.CharField(max_length=64, unique=True, db_index=True)
    slug = models.SlugField(max_length=180, unique=True)
    status = models.CharField(
        max_length=16,
        choices=Status.choices,
        default=Status.DRAFT,
        db_index=True,
    )
    product_kind = models.CharField(
        max_length=32,
        choices=Kind.choices,
        default=Kind.FINISHED_GOOD,
    )
    category = models.ForeignKey(
        "catalog.Category",
        null=True,
        blank=True,
        on_delete=models.SET_NULL,
        related_name="products",
    )
    brand = models.CharField(max_length=120, db_index=True)
    model_code = models.CharField(max_length=120, blank=True, db_index=True)
    price = models.DecimalField(max_digits=12, decimal_places=2, default=0)
    currency = models.CharField(max_length=3, default="BRL")
    voltage = models.CharField(max_length=32, blank=True, db_index=True)
    power_w = models.DecimalField(max_digits=10, decimal_places=2, null=True, blank=True)
    weight_kg = models.DecimalField(max_digits=10, decimal_places=3, null=True, blank=True)
    dimensions = models.JSONField(default=dict, blank=True)
    specs = models.JSONField(default=dict, blank=True)
    manual = models.ForeignKey(
        "manuals.Manual",
        null=True,
        blank=True,
        on_delete=models.SET_NULL,
        related_name="products",
    )
    extraction_confidence = models.FloatField(null=True, blank=True)
    published_at = models.DateTimeField(null=True, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    history = HistoricalRecords()

    class Meta:
        ordering = ("-updated_at",)
        verbose_name = "produto"
        verbose_name_plural = "produtos"
        indexes = [
            models.Index(fields=["status", "brand"]),
            models.Index(fields=["status", "voltage"]),
            models.Index(fields=["status", "model_code"]),
            models.Index(fields=["brand", "status", "sku"]),
            models.Index(fields=["status", "published_at"]),
        ]

    def __str__(self) -> str:
        return f"{self.sku} — {self.brand} {self.model_code}".strip()

    def save(self, *args, **kwargs):
        if not self.slug:
            base = slugify(f"{self.brand}-{self.model_code}-{self.sku}") or self.sku
            self.slug = base[:180]
        if self.status == self.Status.PUBLISHED and self.published_at is None:
            self.published_at = timezone.now()
        if self.status != self.Status.PUBLISHED:
            self.published_at = None
        super().save(*args, **kwargs)

    @property
    def name_pt(self) -> str:
        return self.name_for("pt-BR")

    @property
    def description_pt(self) -> str:
        return self.description_for("pt-BR")

    def name_for(self, locale: str = "pt-BR") -> str:
        tr = self.translations.filter(locale=locale).first()
        if tr is None and locale != "pt-BR":
            tr = self.translations.filter(locale="pt-BR").first()
        return tr.name if tr else f"{self.brand} {self.model_code}"

    def description_for(self, locale: str = "pt-BR") -> str:
        tr = self.translations.filter(locale=locale).first()
        if tr is None and locale != "pt-BR":
            tr = self.translations.filter(locale="pt-BR").first()
        return tr.description if tr else ""

    @property
    def primary_image(self):
        """Primeira imagem com arquivo; prioriza `is_primary`."""
        with_file = self.images.exclude(image="").order_by("sort_order", "id")
        primary = with_file.filter(is_primary=True).first()
        return primary or with_file.first()

    @property
    def quantity_sellable(self) -> int:
        try:
            stock = self.stock
        except Stock.DoesNotExist:
            return 0
        return max(0, stock.quantity_available - stock.quantity_reserved)

    @property
    def in_stock(self) -> bool:
        return self.quantity_sellable > 0


class ProductTranslation(models.Model):
    product = models.ForeignKey(
        Product,
        on_delete=models.CASCADE,
        related_name="translations",
    )
    locale = models.CharField(max_length=10, default="pt-BR")
    name = models.CharField(max_length=255)
    description = models.TextField(blank=True)
    slug = models.SlugField(max_length=180, blank=True)

    class Meta:
        unique_together = ("product", "locale")
        verbose_name = "tradução de produto"
        verbose_name_plural = "traduções de produto"

    def __str__(self) -> str:
        return f"{self.locale}: {self.name}"


def product_image_upload_to(instance: ProductImage, filename: str) -> str:
    safe = filename.replace(" ", "_")
    return f"products/{instance.product_id}/{safe}"


class ProductImage(models.Model):
    product = models.ForeignKey(Product, on_delete=models.CASCADE, related_name="images")
    image = models.ImageField(upload_to=product_image_upload_to, blank=True)
    alt_text = models.CharField(max_length=255, blank=True)
    sort_order = models.PositiveSmallIntegerField(default=0)
    is_primary = models.BooleanField(default=False)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ("sort_order", "id")
        verbose_name = "imagem de produto"
        verbose_name_plural = "imagens de produto"

    def __str__(self) -> str:
        return f"Image #{self.pk} — {self.product.sku}"


class Stock(models.Model):
    product = models.OneToOneField(Product, on_delete=models.CASCADE, related_name="stock")
    quantity_available = models.PositiveIntegerField(default=0)
    quantity_reserved = models.PositiveIntegerField(default=0)
    minimum_alert = models.PositiveIntegerField(default=2)
    updated_at = models.DateTimeField(auto_now=True)
    history = HistoricalRecords()

    class Meta:
        verbose_name = "estoque"
        verbose_name_plural = "estoques"

    def __str__(self) -> str:
        return f"Stock {self.product.sku}: {self.sellable} sellable"

    @property
    def sellable(self) -> int:
        return max(0, self.quantity_available - self.quantity_reserved)

    @property
    def below_minimum(self) -> bool:
        return self.sellable <= self.minimum_alert

    def clean(self):
        if self.quantity_reserved > self.quantity_available:
            raise ValidationError("Reservado não pode exceder disponível.")

    @classmethod
    @transaction.atomic
    def reserve(cls, product_id: int, qty: int) -> Stock:
        """Reserva temporária (checkout) — evita overselling."""
        if qty < 1:
            raise ValidationError("Quantidade inválida.")
        stock = cls.objects.select_for_update().get(product_id=product_id)
        if stock.sellable < qty:
            raise ValidationError("Estoque insuficiente para reserva.")
        stock.quantity_reserved = F("quantity_reserved") + qty
        stock.save(update_fields=["quantity_reserved", "updated_at"])
        stock.refresh_from_db()
        return stock

    @classmethod
    @transaction.atomic
    def release(cls, product_id: int, qty: int) -> Stock:
        if qty < 1:
            raise ValidationError("Quantidade inválida.")
        stock = cls.objects.select_for_update().get(product_id=product_id)
        new_reserved = max(0, stock.quantity_reserved - qty)
        stock.quantity_reserved = new_reserved
        stock.save(update_fields=["quantity_reserved", "updated_at"])
        stock.refresh_from_db()
        return stock

    @classmethod
    @transaction.atomic
    def commit_sale(cls, product_id: int, qty: int) -> Stock:
        """Confirma venda: baixa disponível e libera reserva."""
        if qty < 1:
            raise ValidationError("Quantidade inválida.")
        stock = cls.objects.select_for_update().get(product_id=product_id)
        if stock.quantity_reserved < qty or stock.quantity_available < qty:
            raise ValidationError("Não há reserva/estoque suficiente para baixa.")
        stock.quantity_available = F("quantity_available") - qty
        stock.quantity_reserved = F("quantity_reserved") - qty
        stock.save(update_fields=["quantity_available", "quantity_reserved", "updated_at"])
        stock.refresh_from_db()
        return stock
