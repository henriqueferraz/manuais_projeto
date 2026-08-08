from django import template

from apps.products.specs_display import (
    format_spec_value,
    label_for_spec_key,
    product_spec_rows,
)

register = template.Library()


@register.filter
def spec_label(key) -> str:
    return label_for_spec_key(str(key) if key is not None else "")


@register.filter
def spec_value(value) -> str:
    return format_spec_value(value)


@register.filter
def product_specs(product):
    """Lista de (rótulo, valor) prontos para a PDP."""
    if product is None:
        return []
    return product_spec_rows(product)
