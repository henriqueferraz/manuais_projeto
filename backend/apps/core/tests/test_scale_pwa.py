"""Testes T-P.5 — router de réplica e seed i18n."""

from __future__ import annotations

from decimal import Decimal

import pytest
from django.core.management import call_command
from django.test import override_settings

from apps.core.db_router import PrimaryReplicaRouter
from apps.products.models import Product, ProductTranslation


def test_router_reads_replica_when_configured():
    router = PrimaryReplicaRouter()
    with override_settings(DATABASES={"default": {}, "replica": {}}):
        assert router.db_for_read(Product) == "replica"
        assert router.db_for_write(Product) == "default"
        assert router.allow_migrate("default", "products") is True
        assert router.allow_migrate("replica", "products") is False


def test_router_falls_back_to_default_without_replica():
    router = PrimaryReplicaRouter()
    with override_settings(DATABASES={"default": {}}):
        assert router.db_for_read(Product) == "default"


@pytest.mark.django_db
def test_seed_scale_catalog_creates_en_es():
    call_command("seed_scale_catalog", count=2)
    product = Product.objects.filter(sku__startswith="SCL-").first()
    assert product is not None
    locales = set(
        ProductTranslation.objects.filter(product=product).values_list("locale", flat=True)
    )
    assert "pt-BR" in locales
    assert "en" in locales
    assert "es" in locales
    assert product.price >= Decimal("49.90")
