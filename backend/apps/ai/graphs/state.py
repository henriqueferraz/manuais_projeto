"""Estado tipado do grafo de diagnóstico."""

from __future__ import annotations

from typing import Any, TypedDict


class DiagnosisState(TypedDict, total=False):
    symptom: str
    product_id: int | None
    category_id: int | None
    category_name: str
    product_type: str
    model_code: str
    user_id: int | None
    decision: str  # manual | orders | ask_details | ask_product
    ask_message: str
    chunks: list[dict[str, Any]]
    orders_summary: str
    cause: str
    confidence: float
    ref_manual: str
    recommended_skus: list[str]
    answer: str
    sources: list[dict[str, Any]]
    found_in_manual: bool
    model_name: str
