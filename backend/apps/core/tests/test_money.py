"""Testes da formatação BRL."""

from decimal import Decimal

from apps.core.money import format_brl


def test_format_brl_thousands_and_cents():
    assert format_brl(Decimal("999999")) == "R$ 999.999,00"
    assert format_brl("999999.00") == "R$ 999.999,00"
    assert format_brl(489.9) == "R$ 489,90"
    assert format_brl(10) == "R$ 10,00"
    assert format_brl(0) == "R$ 0,00"


def test_format_brl_without_symbol():
    assert format_brl(Decimal("1500.5"), include_symbol=False) == "1.500,50"


def test_format_brl_negative_and_none():
    assert format_brl(Decimal("-12.3")) == "R$ -12,30"
    assert format_brl(None) == "R$ 0,00"
