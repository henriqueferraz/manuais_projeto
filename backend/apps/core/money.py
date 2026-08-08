"""Formatação monetária BRL compartilhada (exibição)."""

from __future__ import annotations

from decimal import Decimal, InvalidOperation, ROUND_HALF_UP
from typing import Any


def format_brl(value: Any, *, include_symbol: bool = True) -> str:
    """Formata valor no padrão brasileiro: ``R$ 999.999,00``.

    Aceita Decimal, int, float, str numérica ou None.
    """
    amount = _to_decimal(value)
    sign = "-" if amount < 0 else ""
    amount = abs(amount).quantize(Decimal("0.01"), rounding=ROUND_HALF_UP)
    integer_part, _, frac = f"{amount:.2f}".partition(".")
    groups: list[str] = []
    while integer_part:
        groups.append(integer_part[-3:])
        integer_part = integer_part[:-3]
    formatted_int = ".".join(reversed(groups))
    body = f"{sign}{formatted_int},{frac}"
    return f"R$ {body}" if include_symbol else body


def _to_decimal(value: Any) -> Decimal:
    if value is None or value == "":
        return Decimal("0.00")
    if isinstance(value, Decimal):
        return value
    try:
        return Decimal(str(value).replace(",", "."))
    except (InvalidOperation, ValueError, TypeError):
        return Decimal("0.00")
