"""Categorias e modelos de equipamento do catálogo."""

from django.db import models
from django.utils.text import slugify
from simple_history.models import HistoricalRecords


class Category(models.Model):
    """Categoria de produto (ex.: ventiladores de teto, peças)."""

    name = models.CharField(max_length=120)
    slug = models.SlugField(max_length=140, unique=True)
    description = models.TextField(blank=True)
    parent = models.ForeignKey(
        "self",
        null=True,
        blank=True,
        on_delete=models.SET_NULL,
        related_name="children",
    )
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    history = HistoricalRecords()

    class Meta:
        ordering = ("name",)
        verbose_name = "categoria"
        verbose_name_plural = "categorias"

    def __str__(self) -> str:
        return self.name

    def save(self, *args, **kwargs):
        from apps.products.libraries.field_style import initial_cap

        self.name = initial_cap(self.name or "")[:120]
        if not self.slug:
            self.slug = slugify(self.name)[:140]
        super().save(*args, **kwargs)


class Brand(models.Model):
    """Marca do equipamento / peça (ex.: Mondial, Brastemp)."""

    name = models.CharField(max_length=120, unique=True, db_index=True)
    slug = models.SlugField(max_length=140, unique=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    history = HistoricalRecords()

    class Meta:
        ordering = ("name",)
        verbose_name = "marca"
        verbose_name_plural = "marcas"

    def __str__(self) -> str:
        return self.name

    def save(self, *args, **kwargs):
        if not self.slug:
            self.slug = slugify(self.name)[:140] or "marca"
        super().save(*args, **kwargs)


class EquipmentModel(models.Model):
    """Modelo de equipamento (ex.: VTE-02, VT-40-NB) — catálogo de referência."""

    code = models.CharField(max_length=120, unique=True, db_index=True)
    brand = models.CharField(max_length=120, blank=True, db_index=True)
    name = models.CharField(max_length=255, blank=True)
    slug = models.SlugField(max_length=160, unique=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    history = HistoricalRecords()

    class Meta:
        ordering = ("brand", "code")
        verbose_name = "modelo"
        verbose_name_plural = "modelos"

    def __str__(self) -> str:
        if self.brand:
            return f"{self.brand} {self.code}"
        return self.code

    def save(self, *args, **kwargs):
        if not self.slug:
            base = slugify(f"{self.brand}-{self.code}") or slugify(self.code) or "modelo"
            self.slug = base[:160]
        super().save(*args, **kwargs)
