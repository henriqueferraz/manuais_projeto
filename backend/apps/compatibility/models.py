"""Compatibilidade equipamento × peça (ORM, sem LLM)."""

from django.db import models
from simple_history.models import HistoricalRecords


class Compatibility(models.Model):
    """Relação modelo de equipamento → peça de reposição."""

    equipment_brand = models.CharField(max_length=120, db_index=True)
    equipment_model = models.CharField(max_length=120, db_index=True)
    part_product = models.ForeignKey(
        "products.Product",
        on_delete=models.CASCADE,
        related_name="compatibilities",
        limit_choices_to={"product_kind": "spare_part"},
    )
    notes = models.CharField(max_length=255, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    history = HistoricalRecords()

    class Meta:
        ordering = ("equipment_brand", "equipment_model", "part_product_id")
        verbose_name = "compatibilidade"
        verbose_name_plural = "compatibilidades"
        constraints = [
            models.UniqueConstraint(
                fields=["equipment_brand", "equipment_model", "part_product"],
                name="uniq_compat_brand_model_part",
            )
        ]
        indexes = [
            models.Index(
                fields=["equipment_brand", "equipment_model"],
                name="compat_brand_model_idx",
            ),
        ]

    def __str__(self) -> str:
        return f"{self.equipment_brand} {self.equipment_model} → {self.part_product.sku}"
