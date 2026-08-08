"""Testes de rótulos/valores de especificações."""

from __future__ import annotations

from decimal import Decimal

from apps.products.specs_display import (
    format_spec_value,
    label_for_spec_key,
    product_spec_rows,
)


def test_label_for_known_spec_keys():
    assert label_for_spec_key("blade_count") == "Nº de pás"
    assert label_for_spec_key("diameter_cm") == "Diâmetro (cm)"
    assert label_for_spec_key("remote_included") == "Controle remoto incluso"
    assert label_for_spec_key("ncm") == "NCM"


def test_label_humanizes_unknown_keys():
    assert label_for_spec_key("motor_type") == "Motor Type"


def test_format_spec_value_bool_and_decimal():
    assert format_spec_value(True) == "Sim"
    assert format_spec_value(False) == "Não"
    assert format_spec_value(Decimal("120.50")) == "120,5"


def test_product_spec_rows_includes_fields_and_specs():
    class Fake:
        voltage = "220V"
        power_w = Decimal("80")
        weight_kg = None
        dimensions = {"height_cm": 40}
        specs = {"blade_count": 3, "remote_included": True, "ncm": "84145910"}

    rows = dict(product_spec_rows(Fake()))
    assert rows["Voltagem"] == "220V"
    assert rows["Potência (W)"] == "80"
    assert rows["Altura (cm)"] == "40"
    assert rows["Nº de pás"] == "3"
    assert rows["Controle remoto incluso"] == "Sim"
    assert rows["NCM"] == "84145910"
