"""Regra de ouro — normalização de valores inseridos nos campos de produto."""

from __future__ import annotations

import re
from typing import Any

from apps.products.libraries.colors import COLOR_BY_NAME, color_name

_MULTI_SPACE = re.compile(r"\s+")
_VOLTAGE_BIVOLT = re.compile(
    r"(?i)\bbivolt\b|\b127\s*/\s*220(?:\s*v)?\b|\b110\s*/\s*220(?:\s*v)?\b|\b127\s*[-–]\s*220(?:\s*v)?\b"
)
_KNOWN_ACRONYMS = frozenset(
    {
        "ABS",
        "LED",
        "RPM",
        "NCM",
        "EAN",
        "SKU",
        "USB",
        "AC",
        "DC",
        "IP",
        "INMETRO",
    }
)


def collapse_spaces(text: str) -> str:
    return _MULTI_SPACE.sub(" ", (text or "").strip())


def initial_cap(text: str) -> str:
    """Primeira letra alfabética maiúscula; resto preservado (exceto trim/espaços)."""
    value = collapse_spaces(text)
    if not value:
        return ""
    for idx, char in enumerate(value):
        if char.isalpha():
            return value[:idx] + char.upper() + value[idx + 1 :]
    return value


def initial_cap_lines(text: str, *, max_lines: int | None = None) -> str:
    lines = [initial_cap(line) for line in (text or "").splitlines() if collapse_spaces(line)]
    if max_lines is not None:
        lines = lines[:max_lines]
    return "\n".join(lines)


def normalize_sku(value: str) -> str:
    raw = collapse_spaces(value).upper().replace(" ", "-")
    raw = re.sub(r"[^A-Z0-9\-]+", "", raw)
    raw = re.sub(r"-{2,}", "-", raw).strip("-")
    return raw[:64]


def normalize_voltage(value: str) -> str:
    raw = collapse_spaces(value)
    if not raw:
        return ""
    # Bivolt antes de casar 220V isolado (ex.: "127/220V")
    if _VOLTAGE_BIVOLT.search(raw) or re.search(r"(?i)\b127\s*/\s*220", raw) or re.search(
        r"(?i)\b110\s*/\s*220", raw
    ):
        return "Bivolt"
    if re.search(r"(?i)\b220\s*v\b", raw):
        return "220V"
    if re.search(r"(?i)\b(110|127)\s*v\b", raw):
        return "110V"
    # Já canônico?
    canon = raw.upper().replace(" ", "")
    if canon in {"110V", "127V"}:
        return "110V"
    if canon == "220V":
        return "220V"
    if canon == "BIVOLT":
        return "Bivolt"
    return initial_cap(raw)


def normalize_color(value: str) -> str:
    raw = collapse_spaces(value)
    if not raw:
        return ""
    entry = COLOR_BY_NAME.get(raw.casefold())
    if entry:
        return entry["name"]
    # Tenta código 2/3 letras
    named = color_name(raw)
    if named:
        return named
    return initial_cap(raw)


def normalize_material(value: str) -> str:
    raw = collapse_spaces(value)
    if not raw:
        return ""
    upper = raw.upper()
    if upper in _KNOWN_ACRONYMS:
        return upper
    # Sigla pura curta
    if re.fullmatch(r"[A-Za-z]{2,5}", raw) and raw.isupper():
        return raw
    return initial_cap(raw)


def normalize_numeric_display(value: Any) -> Any:
    """Remove unidade acidental em valores que deveriam ser só número."""
    if value in (None, ""):
        return ""
    if isinstance(value, (int, float)):
        return value
    text = collapse_spaces(str(value))
    match = re.match(r"^([+-]?\d+(?:[.,]\d+)?)", text)
    if not match:
        return text
    num = match.group(1).replace(",", ".")
    if "." in num:
        return float(num)
    return int(num)


def apply_field_style(suggestions: dict[str, Any]) -> dict[str, Any]:
    """Aplica a regra de ouro sobre o dict de form_suggestions (in-place + return)."""
    if not suggestions:
        return suggestions

    if "sku" in suggestions and suggestions["sku"]:
        suggestions["sku"] = normalize_sku(str(suggestions["sku"]))

    if "name" in suggestions and suggestions["name"]:
        suggestions["name"] = initial_cap(str(suggestions["name"]))

    if "description" in suggestions and suggestions["description"]:
        suggestions["description"] = initial_cap_lines(
            str(suggestions["description"]), max_lines=4
        )

    if "voltage" in suggestions and suggestions["voltage"]:
        suggestions["voltage"] = normalize_voltage(str(suggestions["voltage"]))

    if "material" in suggestions and suggestions["material"]:
        suggestions["material"] = normalize_material(str(suggestions["material"]))

    if "color" in suggestions and suggestions["color"]:
        suggestions["color"] = normalize_color(str(suggestions["color"]))

    for key in ("mounting", "bearing_type", "brand_name", "category_name", "model_code"):
        if suggestions.get(key):
            if key == "model_code":
                suggestions[key] = collapse_spaces(str(suggestions[key])).upper()
            else:
                suggestions[key] = initial_cap(str(suggestions[key]))

    for key in (
        "power_w",
        "weight_kg",
        "dim_height_cm",
        "dim_width_cm",
        "dim_depth_cm",
        "diameter_cm",
        "blade_count",
        "rpm",
    ):
        if suggestions.get(key) not in (None, ""):
            suggestions[key] = normalize_numeric_display(suggestions[key])

    if suggestions.get("specs_extra"):
        suggestions["specs_extra"] = normalize_specs_extra(str(suggestions["specs_extra"]))

    return suggestions


def normalize_specs_extra(text: str) -> str:
    from apps.products.specs_display import canonicalize_spec_key

    lines: list[str] = []
    for raw in text.splitlines():
        line = collapse_spaces(raw)
        if not line:
            continue
        if "=" in line:
            key, value = line.split("=", 1)
        elif ":" in line:
            key, value = line.split(":", 1)
        else:
            lines.append(initial_cap(line))
            continue
        key = canonicalize_spec_key(collapse_spaces(key))
        value = initial_cap(value)
        if key:
            lines.append(f"{key}={value}")
    return "\n".join(lines[:40])
