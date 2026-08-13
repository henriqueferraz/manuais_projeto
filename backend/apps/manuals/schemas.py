"""Schema Pydantic da saída estruturada da extração (contrato F1 → F3 / prompt v3)."""

from __future__ import annotations

import re
from typing import Any

from pydantic import BaseModel, Field, field_validator, model_validator


class RelatedPartHint(BaseModel):
    """
    Mini-registro de peça/acessório (prompt v3).

    Cada item pode virar Product(spare_part) no approve quando sellable_separately
    e houver `code`. Usado em `spare_parts` e `accessories`.
    """

    code: str = ""
    name: str = ""
    description: str = ""
    sku_suggestion: str = ""
    product_kind: str = "spare_part"
    sellable_separately: bool = True
    ref_number: str = ""
    dimensions: str = ""  # ex.: "400x295x15" / medidas da peça
    qty_per_unit: int | str | None = None
    quantity: int | str | None = None  # alias legado
    compatible_with: list[str] = Field(default_factory=list)
    category: str = ""
    ean: str = ""
    ncm_classification: str = ""
    unit_price: float | None = None
    # Compat v1
    part_code: str = ""
    notes: str = ""

    @field_validator("product_kind", mode="before")
    @classmethod
    def normalize_kind(cls, value: Any) -> str:
        v = str(value or "spare_part").strip().lower()
        return v if v in {"finished_good", "spare_part"} else "spare_part"

    @field_validator("compatible_with", mode="before")
    @classmethod
    def coerce_compatible(cls, value: Any) -> list[str]:
        if not value:
            return []
        if isinstance(value, str):
            return [value.strip()] if value.strip() else []
        return [str(x).strip() for x in value if str(x).strip()]

    @model_validator(mode="after")
    def sync_aliases_and_sellable(self) -> RelatedPartHint:
        if not self.code and self.part_code:
            self.code = self.part_code
        if not self.part_code and self.code:
            self.part_code = self.code
        if not self.description and self.name:
            self.description = self.name
        if not self.name and self.description:
            self.name = self.description
        if self.qty_per_unit is None and self.quantity is not None:
            self.qty_per_unit = self.quantity
        if self.quantity is None and self.qty_per_unit is not None:
            self.quantity = self.qty_per_unit
        if not (self.dimensions or "").strip():
            # Aceita variantes que a LLM às vezes coloca em notes/description
            for blob in (self.notes, self.description, self.name):
                dims = extract_dimensions_token(str(blob or ""))
                if dims:
                    self.dimensions = dims
                    break
        # Sem código → não vende avulso (composição apenas); o pós-processamento
        # pode preencher code sintético (SKU+medidas) e reabilitar a venda.
        if not (self.code or "").strip():
            self.sellable_separately = False
        return self


def extract_dimensions_token(text: str) -> str:
    """Extrai token de medidas (ex.: 400x295x15, 5,0x50mm, M4x20mm, 35mm)."""
    if not text:
        return ""
    metric = re.search(
        r"\bM\s*(\d+)\s*[x×]\s*(\d+(?:[.,]\d+)?)\s*mm\b",
        text,
        flags=re.IGNORECASE,
    )
    if metric:
        return f"M{metric.group(1)}x{metric.group(2).replace(',', '.')}mm"
    match = re.search(
        r"(\d+(?:[.,]\d+)?)\s*[x×]\s*(\d+(?:[.,]\d+)?)" r"(?:\s*[x×]\s*(\d+(?:[.,]\d+)?))?(\s*mm)?",
        text,
        flags=re.IGNORECASE,
    )
    if match:
        parts = [match.group(1).replace(",", "."), match.group(2).replace(",", ".")]
        if match.group(3):
            parts.append(match.group(3).replace(",", "."))
        token = "x".join(parts)
        if match.group(4):
            token = f"{token}mm"
        return token
    simple = re.search(r"(\d+(?:[.,]\d+)?)\s*mm\b", text, flags=re.IGNORECASE)
    if simple:
        return f"{simple.group(1).replace(',', '.')}mm"
    return ""


# Alias públicos usados pelo ExtractedProduct / prompt
SparePartHint = RelatedPartHint
AccessoryHint = RelatedPartHint


class ComponentHint(BaseModel):
    """
    Componente numerado (diagrama / lista de peças de montagem).

    Em guias de montagem (móveis etc.), itens com medidas viram spare_parts
    vendáveis via código sintético SKU+medidas no pós-processamento.
    """

    number: str = ""
    name: str = ""
    description: str = ""
    dimensions: str = ""
    qty_per_unit: int | str | None = None

    @model_validator(mode="after")
    def sync_component_fields(self) -> ComponentHint:
        if not self.description and self.name:
            self.description = self.name
        if not self.name and self.description:
            self.name = self.description
        if not (self.dimensions or "").strip():
            dims = extract_dimensions_token(f"{self.name} {self.description}")
            if dims:
                self.dimensions = dims
        return self


class TroubleshootingHint(BaseModel):
    """Linha de tabela de resolução de problemas / códigos de erro."""

    problem: str = ""
    error_code: str = ""
    cause: str = ""
    solution: str = ""


class WarrantyInfo(BaseModel):
    legal_days: int | None = None
    additional_days: int | None = None
    total_days: int | None = None


class AssemblySummary(BaseModel):
    total_steps: int | None = None
    tools_required: list[str] = Field(default_factory=list)
    hardware_list: list[str] = Field(default_factory=list)


class DocumentConflictHint(BaseModel):
    """Divergência entre trechos/documentos — não escolher silenciosamente (Parte 0 v3)."""

    field: str = ""
    values: list[str] = Field(default_factory=list)
    sources: list[str] = Field(default_factory=list)
    notes: str = ""

    @field_validator("values", "sources", mode="before")
    @classmethod
    def coerce_str_list(cls, value: Any) -> list[str]:
        if not value:
            return []
        if isinstance(value, str):
            return [value.strip()] if value.strip() else []
        return [str(x).strip() for x in value if str(x).strip()]


class ExtractedProduct(BaseModel):
    """JSON estruturado espelhando o schema de produto (prompt v3)."""

    brand: str = Field(..., min_length=1)
    model_code: str = Field(..., min_length=1)
    name: str = Field(..., min_length=1)
    description: str = ""
    sku_suggestion: str = ""
    product_kind: str = Field(default="finished_good")
    category: str = ""
    category_hint: str = ""  # alias legado; preferir `category`
    source_doc_types: list[str] = Field(default_factory=list)
    model_variants: list[str] = Field(default_factory=list)
    voltage: str = ""
    power_w: float | None = None
    frequency_hz: float | None = None
    consumption_kwh: str = ""
    capacity: str = ""
    weight_kg: float | None = None
    dimensions: dict[str, Any] = Field(default_factory=dict)
    dimensions_mm: dict[str, Any] = Field(default_factory=dict)
    ean: str = ""
    barcode: str = ""
    ncm_classification: str = ""
    packaging_qty: int | str | None = None
    specs: dict[str, Any] = Field(default_factory=dict)
    components: list[ComponentHint] = Field(default_factory=list)
    spare_parts: list[RelatedPartHint] = Field(default_factory=list)
    accessories: list[RelatedPartHint] = Field(default_factory=list)
    installation_requirements: list[str] = Field(default_factory=list)
    safety_warnings: list[str] = Field(default_factory=list)
    key_usage_steps: list[str] = Field(default_factory=list)
    troubleshooting: list[TroubleshootingHint] = Field(default_factory=list)
    assembly_summary: AssemblySummary | None = None
    warranty: WarrantyInfo | None = None
    certifications: list[str] = Field(default_factory=list)
    document_conflicts: list[DocumentConflictHint] = Field(default_factory=list)
    notes: str = ""
    low_confidence_fields: list[str] = Field(default_factory=list)
    confidence: float = Field(default=0.5, ge=0.0, le=1.0)
    manufacturer: str = ""

    @field_validator("model_code", mode="before")
    @classmethod
    def coerce_model_code(cls, value: Any) -> str:
        if isinstance(value, list):
            parts = [str(x).strip() for x in value if str(x).strip()]
            return " / ".join(parts) if parts else "SEM-MODELO"
        return str(value or "").strip() or "SEM-MODELO"

    @field_validator("product_kind")
    @classmethod
    def normalize_kind(cls, value: str) -> str:
        allowed = {"finished_good", "spare_part"}
        v = (value or "finished_good").strip().lower()
        return v if v in allowed else "finished_good"

    @field_validator("source_doc_types", mode="before")
    @classmethod
    def normalize_doc_types(cls, value: Any) -> list[str]:
        allowed = {
            "manual",
            "exploded_view",
            "parts_catalog",
            "assembly_guide",
            "spec_sheet",
            "warranty_certificate",
            "other",
        }
        if not value:
            return []
        if isinstance(value, str):
            value = [value]
        out: list[str] = []
        for item in value:
            key = str(item or "").strip().lower()
            if key in allowed and key not in out:
                out.append(key)
        return out

    @field_validator("confidence", mode="before")
    @classmethod
    def clamp_confidence(cls, value: Any) -> float:
        try:
            conf = float(value)
        except (TypeError, ValueError):
            return 0.5
        return max(0.0, min(1.0, conf))

    @model_validator(mode="after")
    def sync_category_and_dimensions(self) -> ExtractedProduct:
        if not self.category and self.category_hint:
            self.category = self.category_hint
        if not self.category_hint and self.category:
            self.category_hint = self.category
        if not self.dimensions and self.dimensions_mm:
            self.dimensions = dict(self.dimensions_mm)
        if not self.dimensions_mm and self.dimensions:
            self.dimensions_mm = dict(self.dimensions)
        if not self.barcode and self.ean:
            self.barcode = self.ean
        if not self.ean and self.barcode:
            self.ean = self.barcode
        return self


class ExtractionResult(BaseModel):
    """Envelope com metadados de custo/modelo."""

    product: ExtractedProduct
    model_name: str = ""
    tokens_in: int = 0
    tokens_out: int = 0
    cost_estimate: float = 0.0
    langsmith_trace_id: str = ""
    prompt_version: str = "v3"
