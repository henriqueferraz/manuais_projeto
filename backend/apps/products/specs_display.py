"""Exibição de especificações técnicas em português (catálogo)."""

from __future__ import annotations

from decimal import Decimal
from typing import Any

SPEC_LABELS_PT: dict[str, str] = {
    "blade_count": "Nº de pás",
    "diameter_cm": "Diâmetro (cm)",
    "material": "Material",
    "color": "Cor",
    "rpm": "RPM",
    "mounting": "Fixação / montagem",
    "bearing_type": "Tipo de rolamento",
    "remote_included": "Controle remoto incluso",
    "ncm": "NCM",
    "power_w": "Potência (W)",
    "weight_kg": "Peso (kg)",
    "voltage": "Voltagem",
    "height_cm": "Altura (cm)",
    "width_cm": "Largura (cm)",
    "depth_cm": "Profundidade (cm)",
    "height": "Altura",
    "width": "Largura",
    "depth": "Profundidade",
    "altura_cm": "Altura (cm)",
    "largura_cm": "Largura (cm)",
    "profundidade_cm": "Profundidade (cm)",
}


def label_for_spec_key(key: str) -> str:
    """Retorna rótulo em português; fallback humanizado se a chave for desconhecida."""
    normalized = (key or "").strip()
    if not normalized:
        return ""
    if normalized in SPEC_LABELS_PT:
        return SPEC_LABELS_PT[normalized]
    lower = normalized.lower()
    if lower in SPEC_LABELS_PT:
        return SPEC_LABELS_PT[lower]
    # chave_livre → Chave livre
    words = normalized.replace("-", "_").split("_")
    return " ".join(w[:1].upper() + w[1:] for w in words if w)


def format_spec_value(value: Any) -> str:
    if value is None:
        return ""
    if isinstance(value, bool):
        return "Sim" if value else "Não"
    if isinstance(value, int) and not isinstance(value, bool):
        return str(value)
    if isinstance(value, Decimal):
        normalized = value.normalize()
        text = format(normalized, "f")
        if "." in text:
            text = text.rstrip("0").rstrip(".")
        return text.replace(".", ",")
    if isinstance(value, float):
        text = f"{value:.10g}"
        return text.replace(".", ",")
    if isinstance(value, (list, tuple)):
        return ", ".join(format_spec_value(item) for item in value)
    if isinstance(value, dict):
        return ", ".join(
            f"{label_for_spec_key(str(k))}: {format_spec_value(v)}" for k, v in value.items()
        )
    text = str(value).strip()
    lowered = text.lower()
    if lowered in {"true", "yes", "sim"}:
        return "Sim"
    if lowered in {"false", "no", "nao", "não"}:
        return "Não"
    return text


def product_spec_rows(product) -> list[tuple[str, str]]:
    """
    Linhas (rótulo, valor) para a PDP: campos técnicos do produto + specs JSON.
    """
    rows: list[tuple[str, str]] = []
    seen_labels: set[str] = set()

    def add(key: str, value: Any) -> None:
        if value in (None, "", {}, []):
            return
        label = label_for_spec_key(key)
        if not label or label in seen_labels:
            return
        formatted = format_spec_value(value)
        if not formatted:
            return
        seen_labels.add(label)
        rows.append((label, formatted))

    add("voltage", getattr(product, "voltage", None))
    add("power_w", getattr(product, "power_w", None))
    add("weight_kg", getattr(product, "weight_kg", None))

    dimensions = getattr(product, "dimensions", None) or {}
    if isinstance(dimensions, dict):
        for key, value in dimensions.items():
            add(str(key), value)

    specs = getattr(product, "specs", None) or {}
    if isinstance(specs, dict):
        for key, value in specs.items():
            add(str(key), value)

    return rows
