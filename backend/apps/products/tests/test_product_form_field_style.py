"""Testes da regra de ouro no InternalProductForm."""

from __future__ import annotations

import pytest

from apps.catalog.models import Brand, Category
from apps.products.forms import InternalProductForm


@pytest.mark.django_db
def test_internal_product_form_applies_field_style():
    brand = Brand.objects.create(name="Mondial", slug="mondial")
    cat = Category.objects.create(name="Ventiladores", slug="ventiladores")
    form = InternalProductForm(
        data={
            "sku": "mondial vte 02",
            "brand_ref": brand.pk,
            "name": "ventilador de teto",
            "description": "linha um\nlinha dois\nlinha três\nlinha quatro\nlinha cinco",
            "price": "99.90",
            "voltage": "127/220V",
            "product_kind": "finished_good",
            "status": "draft",
            "category": cat.pk,
            "quantity_available": 1,
            "minimum_alert": 1,
            "material": "abs",
            "color": "preto",
            "mounting": "fixação no teto",
            "bearing_type": "rolamento selado",
            "specs_extra": "Nivel de ruido: baixo",
        }
    )
    assert form.is_valid(), form.errors
    assert form.cleaned_data["sku"] == "MONDIAL-VTE-02"
    assert form.cleaned_data["name"] == "Ventilador de teto"
    assert form.cleaned_data["description"] == "Linha um\nLinha dois\nLinha três\nLinha quatro"
    assert form.cleaned_data["voltage"] == "Bivolt"
    assert form.cleaned_data["material"] == "ABS"
    assert form.cleaned_data["color"] == "Preto"
    assert form.cleaned_data["mounting"] == "Fixação no teto"
    assert form.cleaned_data["bearing_type"] == "Rolamento selado"
    assert form.cleaned_data["specs_extra"] == "nivel_de_ruido=Baixo"
    assert form.cleaned_specs()["material"] == "ABS"
    assert form.cleaned_specs()["nivel_de_ruido"] == "Baixo"
