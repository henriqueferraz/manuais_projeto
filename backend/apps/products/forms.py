"""Forms de produto / estoque (gestão interna)."""

from __future__ import annotations

import re
from typing import Any

from django import forms

from apps.catalog.models import Brand, Category, EquipmentModel
from apps.products.models import Product

_SKU_RE = re.compile(r"^[A-Z0-9-]+$")

# Chaves de specs com campos dedicados no formulário.
KNOWN_SPEC_KEYS = (
    "blade_count",
    "diameter_cm",
    "material",
    "color",
    "rpm",
    "mounting",
    "bearing_type",
    "remote_included",
)


def _dim_value(dimensions: dict[str, Any], *keys: str) -> Any:
    for key in keys:
        if key in dimensions and dimensions[key] not in (None, ""):
            return dimensions[key]
    return None


def format_specs_extra(specs: dict[str, Any] | None) -> str:
    if not specs:
        return ""
    lines: list[str] = []
    for key, value in specs.items():
        if key in KNOWN_SPEC_KEYS:
            continue
        lines.append(f"{key}: {value}")
    return "\n".join(lines)


def parse_specs_extra(text: str) -> dict[str, Any]:
    result: dict[str, Any] = {}
    for raw_line in (text or "").splitlines():
        line = raw_line.strip()
        if not line or line.startswith("#"):
            continue
        if ":" in line:
            key, value = line.split(":", 1)
        elif "=" in line:
            key, value = line.split("=", 1)
        else:
            raise forms.ValidationError(
                f'Linha inválida em specs extras: "{line}". Use "chave: valor".'
            )
        key = key.strip()
        value = value.strip()
        if not key:
            raise forms.ValidationError("Chave vazia em specs extras.")
        result[key] = _coerce_spec_value(value)
    return result


def _coerce_spec_value(value: str) -> Any:
    lowered = value.lower()
    if lowered in {"true", "sim", "yes"}:
        return True
    if lowered in {"false", "nao", "não", "no"}:
        return False
    try:
        if "." in value or "," in value:
            return float(value.replace(",", "."))
        return int(value)
    except ValueError:
        return value


def build_specs_from_cleaned(data: dict[str, Any]) -> dict[str, Any]:
    specs: dict[str, Any] = {}
    if data.get("blade_count") is not None:
        specs["blade_count"] = data["blade_count"]
    if data.get("diameter_cm") is not None:
        specs["diameter_cm"] = float(data["diameter_cm"])
    for key in ("material", "color", "rpm", "mounting", "bearing_type"):
        value = (data.get(key) or "").strip()
        if value:
            specs[key] = value
    if data.get("remote_included"):
        specs["remote_included"] = True
    specs.update(data.get("specs_extra_parsed") or {})
    return specs


def build_dimensions_from_cleaned(data: dict[str, Any]) -> dict[str, Any]:
    dims: dict[str, Any] = {}
    mapping = (
        ("dim_height_cm", "height_cm"),
        ("dim_width_cm", "width_cm"),
        ("dim_depth_cm", "depth_cm"),
    )
    for form_key, dim_key in mapping:
        value = data.get(form_key)
        if value is not None:
            dims[dim_key] = float(value)
    return dims


def initial_specs_from_product(product: Product) -> dict[str, Any]:
    specs = product.specs if isinstance(product.specs, dict) else {}
    dims = product.dimensions if isinstance(product.dimensions, dict) else {}
    remote = specs.get("remote_included")
    return {
        "power_w": product.power_w,
        "weight_kg": product.weight_kg,
        "dim_height_cm": _dim_value(dims, "height_cm", "height", "altura_cm", "altura"),
        "dim_width_cm": _dim_value(dims, "width_cm", "width", "largura_cm", "largura"),
        "dim_depth_cm": _dim_value(dims, "depth_cm", "depth", "profundidade_cm", "profundidade"),
        "blade_count": specs.get("blade_count"),
        "diameter_cm": specs.get("diameter_cm"),
        "material": specs.get("material") or "",
        "color": specs.get("color") or "",
        "rpm": "" if specs.get("rpm") is None else str(specs.get("rpm")),
        "mounting": specs.get("mounting") or "",
        "bearing_type": specs.get("bearing_type") or "",
        "remote_included": bool(remote) if remote not in (None, "", 0, "0", "false", "não", "nao") else False,
        "specs_extra": format_specs_extra(specs),
    }


class InternalProductForm(forms.Form):
    sku = forms.CharField(
        label="SKU",
        max_length=64,
        help_text="Somente A–Z, 0–9 e hífen (-). Sem espaços.",
        widget=forms.TextInput(
            attrs={
                "class": "form-control",
                "pattern": "[A-Za-z0-9-]+",
                "title": "Apenas letras, números e hífen (salvo em maiúsculas)",
                "autocomplete": "off",
                "spellcheck": "false",
                "autocapitalize": "characters",
                "style": "text-transform: uppercase;",
            }
        ),
    )
    brand_ref = forms.ModelChoiceField(
        label="Marca",
        queryset=Brand.objects.all(),
        required=True,
        empty_label="Selecione a marca",
    )
    equipment_model = forms.ModelChoiceField(
        label="Modelo",
        queryset=EquipmentModel.objects.all(),
        required=False,
        empty_label="Selecione o modelo",
    )
    name = forms.CharField(label="Nome (pt-BR)", max_length=255)
    description = forms.CharField(
        label="Descrição (pt-BR)",
        widget=forms.Textarea,
        required=False,
    )
    price = forms.DecimalField(
        label="Preço",
        max_digits=12,
        decimal_places=2,
        min_value=0,
    )
    voltage = forms.CharField(label="Voltagem", max_length=32, required=False)
    product_kind = forms.ChoiceField(label="Tipo", choices=Product.Kind.choices)
    status = forms.ChoiceField(label="Status", choices=Product.Status.choices)
    category = forms.ModelChoiceField(
        label="Categoria",
        queryset=Category.objects.all(),
        required=False,
        empty_label="Selecione a categoria",
    )
    quantity_available = forms.IntegerField(
        label="Estoque disponível",
        min_value=0,
        initial=0,
    )
    minimum_alert = forms.IntegerField(
        label="Alerta mínimo",
        min_value=0,
        initial=2,
    )

    power_w = forms.DecimalField(
        label="Potência (W)",
        max_digits=10,
        decimal_places=2,
        required=False,
        min_value=0,
    )
    weight_kg = forms.DecimalField(
        label="Peso (kg)",
        max_digits=10,
        decimal_places=3,
        required=False,
        min_value=0,
    )
    dim_height_cm = forms.DecimalField(
        label="Altura (cm)",
        max_digits=10,
        decimal_places=2,
        required=False,
        min_value=0,
    )
    dim_width_cm = forms.DecimalField(
        label="Largura (cm)",
        max_digits=10,
        decimal_places=2,
        required=False,
        min_value=0,
    )
    dim_depth_cm = forms.DecimalField(
        label="Profundidade (cm)",
        max_digits=10,
        decimal_places=2,
        required=False,
        min_value=0,
    )
    blade_count = forms.IntegerField(label="Nº de pás", required=False, min_value=0)
    diameter_cm = forms.DecimalField(
        label="Diâmetro (cm)",
        max_digits=10,
        decimal_places=2,
        required=False,
        min_value=0,
    )
    material = forms.CharField(label="Material", max_length=120, required=False)
    color = forms.CharField(label="Cor", max_length=80, required=False)
    rpm = forms.CharField(label="RPM", max_length=64, required=False)
    mounting = forms.CharField(label="Fixação / montagem", max_length=120, required=False)
    bearing_type = forms.CharField(label="Tipo de rolamento", max_length=120, required=False)
    remote_included = forms.BooleanField(label="Controle remoto incluso", required=False)
    specs_extra = forms.CharField(
        label="Specs extras",
        required=False,
        widget=forms.Textarea,
        help_text='Uma por linha no formato "chave: valor" (ex.: ncm: 84145910).',
    )

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields["brand_ref"].queryset = Brand.objects.order_by("name")
        self.fields["equipment_model"].queryset = EquipmentModel.objects.order_by(
            "brand", "code"
        )
        self.fields["category"].queryset = Category.objects.order_by("name")
        for name, field in self.fields.items():
            if name == "sku":
                continue
            if isinstance(field.widget, forms.CheckboxInput):
                field.widget.attrs.setdefault("class", "form-check-input")
                continue
            css = "form-control"
            if isinstance(field.widget, forms.Select):
                css = "form-select"
            if isinstance(field.widget, forms.Textarea):
                field.widget.attrs["rows"] = 4 if name != "specs_extra" else 5
            field.widget.attrs.setdefault("class", css)

    def clean_sku(self) -> str:
        raw = self.cleaned_data.get("sku") or ""
        sku = raw.strip().upper()
        if not sku:
            raise forms.ValidationError("Informe o SKU.")
        if any(ch.isspace() for ch in sku):
            raise forms.ValidationError(
                "O SKU não pode conter espaços. Use apenas letras maiúsculas, números e hífen (-)."
            )
        if not _SKU_RE.fullmatch(sku):
            raise forms.ValidationError(
                "Use apenas letras maiúsculas, números e hífen (-). "
                "Sem espaços ou caracteres especiais."
            )
        return sku

    def clean_specs_extra(self) -> str:
        text = self.cleaned_data.get("specs_extra") or ""
        parsed = parse_specs_extra(text)
        overlap = sorted(set(parsed) & set(KNOWN_SPEC_KEYS))
        if overlap:
            raise forms.ValidationError(
                "Estas chaves já têm campo próprio: "
                + ", ".join(overlap)
                + ". Remova-as de specs extras."
            )
        self.cleaned_data["specs_extra_parsed"] = parsed
        return text

    def cleaned_specs(self) -> dict[str, Any]:
        data = dict(self.cleaned_data)
        if "specs_extra_parsed" not in data:
            data["specs_extra_parsed"] = parse_specs_extra(data.get("specs_extra") or "")
        return build_specs_from_cleaned(data)

    def cleaned_dimensions(self) -> dict[str, Any]:
        return build_dimensions_from_cleaned(self.cleaned_data)
