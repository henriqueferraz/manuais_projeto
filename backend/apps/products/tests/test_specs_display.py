"""Testes de rótulos/valores de especificações."""

from __future__ import annotations

from decimal import Decimal

from apps.products.specs_display import (
    canonicalize_spec_key,
    format_spec_value,
    label_for_spec_key,
    product_spec_rows,
)


def test_label_for_known_spec_keys():
    assert label_for_spec_key("blade_count") == "Nº de pás"
    assert label_for_spec_key("diameter_cm") == "Diâmetro (cm)"
    assert label_for_spec_key("remote_included") == "Controle remoto incluso"
    assert label_for_spec_key("ncm") == "NCM"
    assert label_for_spec_key("safety_warnings") == "Avisos de segurança"
    assert label_for_spec_key("key_usage_steps") == "Como utilizar"
    assert label_for_spec_key("warranty.legal_days") == "Garantia legal (dias)"
    assert label_for_spec_key("warranty_total_days") == "Garantia total (dias)"


def test_label_humanizes_unknown_keys():
    assert label_for_spec_key("motor_type") == "Motor type"
    assert label_for_spec_key("noise_level") == "Noise level"


def test_canonicalize_spec_key_dots_and_case():
    assert canonicalize_spec_key("Warranty.Legal_Days") == "warranty_legal_days"
    assert canonicalize_spec_key("key_usage_steps") == "key_usage_steps"
    assert canonicalize_spec_key("Potencia") == "power_w"
    assert canonicalize_spec_key("potência") == "power_w"
    assert label_for_spec_key("Potencia") == "Potência (W)"


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


def test_product_spec_rows_warranty_deduped_and_portuguese():
    class Fake:
        voltage = "127V"
        power_w = None
        weight_kg = None
        dimensions = {}
        specs = {
            "warranty": {
                "Legal_days": 90,
                "total_days": 360,
                "additional_days": 270,
            },
            "warranty.legal_days": 90,
            "warranty.total_days": 360,
            "warranty.additional_days": 270,
            "key_usage_steps": "Encaixe o copo; Selecione a velocidade",
            "safety_warnings": "Não ligue vazio; Desligue da tomada",
            "installation_requirements": "Local plano e seco",
            "source_doc_types": ["manual", "warranty_certificate"],
        }

    rows = product_spec_rows(Fake())
    labels = [label for label, _ in rows]
    values = dict(rows)

    assert "Garantia" not in labels  # não mostra o dict cru
    assert labels.count("Garantia legal (dias)") == 1
    assert labels.count("Garantia total (dias)") == 1
    assert labels.count("Garantia adicional (dias)") == 1
    assert values["Garantia legal (dias)"] == "90"
    assert values["Garantia total (dias)"] == "360"
    assert values["Como utilizar"].startswith("Encaixe")
    assert values["Avisos de segurança"].startswith("Não ligue")
    assert values["Requisitos de instalação"] == "Local plano e seco"
    assert "Source Doc Types" not in labels
    assert "source_doc_types" not in labels
