"""Fixtures E2E — live_server Django + produto seed."""

from __future__ import annotations

import os

# Playwright/pytest-playwright roda em loop async; Django sync DB precisa disto.
os.environ.setdefault("DJANGO_ALLOW_ASYNC_UNSAFE", "true")

import pytest


@pytest.fixture
def e2e_product(db):
    from apps.catalog.models import Category
    from apps.products.models import Product, ProductTranslation, Stock

    cat = Category.objects.create(name="E2E", slug="e2e-cat")
    product = Product.objects.create(
        sku="E2E-001",
        brand="Mondial",
        model_code="VTE-02",
        price="89.90",
        status=Product.Status.PUBLISHED,
        category=cat,
        weight_kg="0.5",
        slug="e2e-ventilador-peca",
    )
    ProductTranslation.objects.create(
        product=product, locale="pt-BR", name="Peça E2E ventilador"
    )
    Stock.objects.create(product=product, quantity_available=10, quantity_reserved=0)
    return product


@pytest.fixture(scope="session")
def browser_context_args(browser_context_args):
    return {**browser_context_args, "locale": "pt-BR"}
