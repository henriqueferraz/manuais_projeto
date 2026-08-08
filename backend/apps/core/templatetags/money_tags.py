"""Filtros de template para formatação monetária."""

from django import template

from apps.core.money import format_brl

register = template.Library()


@register.filter(name="brl")
def brl(value) -> str:
    """Exibe preço no padrão ``R$ 999.999,00``."""
    return format_brl(value)
