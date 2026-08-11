"""Biblioteca de cores com abreviaturas de 2 e 3 letras.

Lista normativa (3 letras) + abreviaturas curtas (2 letras).
Uso típico: sufixo de SKU / especificação de produto (`specs.color`).
"""

from __future__ import annotations

from typing import NotRequired, TypedDict


class ColorEntry(TypedDict):
    name: str
    code2: str
    code3: NotRequired[str]
    code3_alts: NotRequired[tuple[str, ...]]
    aliases: NotRequired[tuple[str, ...]]


COLORS: tuple[ColorEntry, ...] = (
    {
        "name": "Amarelo",
        "code2": "AM",
        "code3": "AMR",
    },
    {
        "name": "Azul",
        "code2": "AZ",
        "code3": "AZL",
    },
    {
        "name": "Branco",
        "code2": "BR",
        "code3": "BRN",
        "code3_alts": ("BRA",),
    },
    {
        "name": "Cinza",
        "code2": "CZ",
        "code3": "CIN",
        "aliases": ("Cinzento",),
    },
    {
        "name": "Laranja",
        "code2": "LR",
        "code3": "LAR",
    },
    {
        "name": "Marrom",
        "code2": "CT",
        "code3": "MAR",
        "aliases": ("Castanho",),
    },
    {
        "name": "Preto",
        "code2": "PT",
        "code3": "PRT",
        "code3_alts": ("PTO",),
    },
    {
        "name": "Rosa",
        "code2": "RS",
        "code3": "RSA",
    },
    {
        "name": "Verde",
        "code2": "VD",
        "code3": "VRD",
    },
    {
        "name": "Vermelho",
        "code2": "VM",
        "code3": "VMH",
    },
    {
        "name": "Violeta",
        "code2": "VT",
        "code3": "VLT",
    },
    # Cores extras do catálogo (apenas 2 letras)
    {"name": "Turquesa", "code2": "TQ"},
    {"name": "Ouro", "code2": "OU"},
    {"name": "Prata", "code2": "PR"},
)

COLOR_BY_CODE: dict[str, str] = {}
COLOR_BY_NAME: dict[str, ColorEntry] = {}

for _entry in COLORS:
    COLOR_BY_CODE[_entry["code2"]] = _entry["name"]
    if code3 := _entry.get("code3"):
        COLOR_BY_CODE[code3] = _entry["name"]
    for alt in _entry.get("code3_alts", ()):
        COLOR_BY_CODE[alt] = _entry["name"]

    COLOR_BY_NAME[_entry["name"].casefold()] = _entry
    for alias in _entry.get("aliases", ()):
        COLOR_BY_NAME[alias.casefold()] = _entry


def abbreviate_color(name: str, *, length: int = 2) -> str | None:
    """Retorna a abreviatura da cor (2 ou 3 letras), ou None."""
    key = (name or "").strip().casefold()
    if not key:
        return None
    entry = COLOR_BY_NAME.get(key)
    if not entry:
        return None
    if length == 2:
        return entry["code2"]
    if length == 3:
        return entry.get("code3")
    raise ValueError("length deve ser 2 ou 3")


def color_name(code: str) -> str | None:
    """Retorna o nome da cor para a abreviatura (2 ou 3 letras), ou None."""
    key = (code or "").strip().upper()
    if not key:
        return None
    return COLOR_BY_CODE.get(key)


def color_choices(*, length: int = 2) -> list[tuple[str, str]]:
    """Choices Django: (código, nome). Preferência: abreviatura primária."""
    if length not in (2, 3):
        raise ValueError("length deve ser 2 ou 3")
    choices: list[tuple[str, str]] = []
    for entry in COLORS:
        code = entry["code2"] if length == 2 else entry.get("code3")
        if code:
            choices.append((code, entry["name"]))
    return choices
