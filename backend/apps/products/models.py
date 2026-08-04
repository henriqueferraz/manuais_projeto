"""Produto mínimo para rascunhos da extração (F3); catálogo completo na F4a."""

from django.db import models
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
    brand = models.CharField(max_length=120)
    model_code = models.CharField(max_length=120, blank=True, db_index=True)
    price = models.DecimalField(max_digits=12, decimal_places=2, default=0)
    currency = models.CharField(max_length=3, default="BRL")
    voltage = models.CharField(max_length=32, blank=True)
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

    def __str__(self) -> str:
        return f"{self.sku} — {self.brand} {self.model_code}".strip()

    def save(self, *args, **kwargs):
        if not self.slug:
            base = slugify(f"{self.brand}-{self.model_code}-{self.sku}") or self.sku
            self.slug = base[:180]
        super().save(*args, **kwargs)

    @property
    def name_pt(self) -> str:
        tr = self.translations.filter(locale="pt-BR").first()
        return tr.name if tr else f"{self.brand} {self.model_code}"


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
