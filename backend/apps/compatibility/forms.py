"""Forms internos de operação (F4a.5)."""

from django import forms

from apps.catalog.models import Category
from apps.compatibility.models import Compatibility
from apps.products.models import Product


class InternalProductForm(forms.Form):
    sku = forms.CharField(max_length=64)
    brand = forms.CharField(max_length=120)
    model_code = forms.CharField(max_length=120, required=False)
    name = forms.CharField(max_length=255)
    description = forms.CharField(widget=forms.Textarea, required=False)
    price = forms.DecimalField(max_digits=12, decimal_places=2, min_value=0)
    voltage = forms.CharField(max_length=32, required=False)
    product_kind = forms.ChoiceField(choices=Product.Kind.choices)
    status = forms.ChoiceField(choices=Product.Status.choices)
    category = forms.ModelChoiceField(queryset=Category.objects.all(), required=False)
    quantity_available = forms.IntegerField(min_value=0, initial=0)
    minimum_alert = forms.IntegerField(min_value=0, initial=2)

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        for _name, field in self.fields.items():
            css = "form-control"
            if isinstance(field.widget, forms.Select):
                css = "form-select"
            if isinstance(field.widget, forms.Textarea):
                field.widget.attrs["rows"] = 4
            field.widget.attrs.setdefault("class", css)


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
