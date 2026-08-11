"""Bibliotecas de referência do catálogo (cores, estilo de campos, etc.)."""

from apps.products.libraries.colors import (
    COLOR_BY_CODE,
    COLOR_BY_NAME,
    COLORS,
    abbreviate_color,
    color_choices,
    color_name,
)
from apps.products.libraries.field_style import (
    apply_field_style,
    initial_cap,
    initial_cap_lines,
    normalize_color,
    normalize_sku,
    normalize_specs_extra,
    normalize_voltage,
)

__all__ = [
    "COLORS",
    "COLOR_BY_CODE",
    "COLOR_BY_NAME",
    "abbreviate_color",
    "apply_field_style",
    "color_choices",
    "color_name",
    "initial_cap",
    "initial_cap_lines",
    "normalize_color",
    "normalize_sku",
    "normalize_specs_extra",
    "normalize_voltage",
]
