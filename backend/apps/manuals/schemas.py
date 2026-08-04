"""Schema Pydantic da saída estruturada da extração (contrato F1 → F3)."""

from __future__ import annotations

from typing import Any

from pydantic import BaseModel, Field, field_validator


class SparePartHint(BaseModel):
    """Peça mencionada no manual (vira rascunho spare_part + compatibilidade na F4a)."""

    name: str
    part_code: str = ""
    notes: str = ""


class ExtractedProduct(BaseModel):
    """JSON estruturado espelhando o schema mínimo de produto."""

    brand: str = Field(..., min_length=1)
    model_code: str = Field(..., min_length=1)
    name: str = Field(..., min_length=1)
    description: str = ""
    sku_suggestion: str = ""
    product_kind: str = Field(default="finished_good")
    category_hint: str = ""
    voltage: str = ""
    power_w: float | None = None
    weight_kg: float | None = None
    dimensions: dict[str, Any] = Field(default_factory=dict)
    specs: dict[str, Any] = Field(default_factory=dict)
    spare_parts: list[SparePartHint] = Field(default_factory=list)
    confidence: float = Field(default=0.5, ge=0.0, le=1.0)
    manufacturer: str = ""

    @field_validator("product_kind")
    @classmethod
    def normalize_kind(cls, value: str) -> str:
        allowed = {"finished_good", "spare_part"}
        v = (value or "finished_good").strip().lower()
        return v if v in allowed else "finished_good"

    @field_validator("confidence", mode="before")
    @classmethod
    def clamp_confidence(cls, value: Any) -> float:
        try:
            conf = float(value)
        except (TypeError, ValueError):
            return 0.5
        return max(0.0, min(1.0, conf))


class ExtractionResult(BaseModel):
    """Envelope com metadados de custo/modelo."""

    product: ExtractedProduct
    model_name: str = ""
    tokens_in: int = 0
    tokens_out: int = 0
    cost_estimate: float = 0.0
    langsmith_trace_id: str = ""
    prompt_version: str = "v1"
