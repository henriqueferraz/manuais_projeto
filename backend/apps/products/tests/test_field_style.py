"""Testes da regra de ouro de campos de produto."""

from apps.products.libraries.field_style import (
    apply_field_style,
    initial_cap,
    initial_cap_lines,
    normalize_color,
    normalize_sku,
    normalize_voltage,
)


def test_initial_cap():
    assert initial_cap("ventilador de teto") == "Ventilador de teto"
    assert initial_cap("  abs  ") == "Abs"
    assert initial_cap("") == ""


def test_initial_cap_lines_max_four():
    text = "uma\nduas\ntrês\nquatro\ncinco"
    out = initial_cap_lines(text, max_lines=4)
    assert out == "Uma\nDuas\nTrês\nQuatro"


def test_normalize_sku_and_voltage_and_color():
    assert normalize_sku("mondial vte-02") == "MONDIAL-VTE-02"
    assert normalize_voltage("127/220V") == "Bivolt"
    assert normalize_voltage("220 v") == "220V"
    assert normalize_color("preto") == "Preto"
    assert normalize_color("PT") == "Preto"


def test_apply_field_style_bundle():
    sug = apply_field_style(
        {
            "sku": "abc 123",
            "name": "hélice abs",
            "description": "linha um\nlinha dois",
            "voltage": "bivolt",
            "material": "abs",
            "color": "azul",
            "power_w": "120 W",
            "mounting": "fixação no teto",
            "specs_extra": "ruido: baixo",
        }
    )
    assert sug["sku"] == "ABC-123"
    assert sug["name"] == "Hélice abs"
    assert sug["description"] == "Linha um\nLinha dois"
    assert sug["voltage"] == "Bivolt"
    assert sug["material"] == "ABS"
    assert sug["color"] == "Azul"
    assert sug["power_w"] == 120
    assert sug["mounting"] == "Fixação no teto"
    assert sug["specs_extra"] == "ruido=Baixo"
