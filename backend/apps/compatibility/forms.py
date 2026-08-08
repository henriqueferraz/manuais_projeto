"""Forms internos de operação (F4a.5)."""

from django import forms

from apps.compatibility.models import Compatibility
from apps.products.forms import InternalProductForm  # noqa: F401 — reexport
from apps.products.models import Product


class CompatibilityForm(forms.ModelForm):
    class Meta:
        model = Compatibility
        fields = ("equipment_brand", "equipment_model", "part_product", "notes")

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields["part_product"].queryset = Product.objects.filter(
            product_kind=Product.Kind.SPARE_PART
        ).order_by("sku")
        for field in self.fields.values():
            if isinstance(field.widget, forms.Select):
                field.widget.attrs["class"] = "form-select"
            else:
                field.widget.attrs["class"] = "form-control"
