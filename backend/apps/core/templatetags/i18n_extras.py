from django import template

register = template.Library()


@register.filter
def name_for_locale(product, locale="pt-BR"):
    if product is None:
        return ""
    return product.name_for(locale or "pt-BR")


@register.filter
def description_for_locale(product, locale="pt-BR"):
    if product is None:
        return ""
    return product.description_for(locale or "pt-BR")
