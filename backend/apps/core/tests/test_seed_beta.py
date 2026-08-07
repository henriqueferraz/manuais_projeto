"""seed_beta — ambiente mínimo para T-P.1."""

from __future__ import annotations

import pytest
from django.contrib.auth import get_user_model
from django.core.management import call_command
from django.core.management.base import CommandError

from apps.ai.models import ManualChunk
from apps.compatibility.models import Compatibility
from apps.products.models import Product

User = get_user_model()


@pytest.mark.django_db
def test_seed_beta_creates_users_products_and_chunks(settings):
    settings.DEBUG = True
    call_command("seed_beta")

    assert User.objects.filter(username="beta.staff@techparts.local", is_staff=True).exists()
    assert User.objects.filter(username="beta.tester@techparts.local", is_staff=False).exists()

    equipment = Product.objects.get(sku="VTE-02")
    part = Product.objects.get(sku="CAP-35")
    assert equipment.status == Product.Status.PUBLISHED
    assert part.in_stock
    assert Compatibility.objects.filter(
        equipment_brand="Mondial",
        equipment_model="VTE-02",
        part_product=part,
    ).exists()
    assert ManualChunk.objects.filter(product=equipment).count() >= 1
    assert equipment.images.filter(is_primary=True).exists()
    assert part.images.filter(is_primary=True).exists()

    # idempotente
    call_command("seed_beta")
    assert Product.objects.filter(sku="VTE-02").count() == 1
    assert Product.objects.filter(sku="CAP-35").count() == 1
    assert equipment.images.count() == 1
    assert part.images.count() == 1


@pytest.mark.django_db
def test_seed_beta_refuses_without_debug(settings):
    settings.DEBUG = False
    with pytest.raises(CommandError, match="DEBUG=False"):
        call_command("seed_beta")
