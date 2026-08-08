"""Testes das regras e normalização de foto de produto."""

from __future__ import annotations

from io import BytesIO

import pytest
from django.core.exceptions import ValidationError
from django.core.files.uploadedfile import SimpleUploadedFile
from PIL import Image

from apps.products.image_validation import (
    PRODUCT_IMAGE_MAX_BYTES,
    PRODUCT_IMAGE_MAX_SIDE,
    PRODUCT_IMAGE_MIN_SIDE,
    prepare_product_image,
    validate_product_image,
)


def _make_image(
    *,
    width: int = 800,
    height: int = 800,
    fmt: str = "JPEG",
    name: str = "foto.jpg",
    content_type: str = "image/jpeg",
) -> SimpleUploadedFile:
    buf = BytesIO()
    Image.new("RGB", (width, height), color=(20, 40, 60)).save(buf, format=fmt)
    return SimpleUploadedFile(name, buf.getvalue(), content_type=content_type)


def test_validate_product_image_ok():
    validate_product_image(_make_image())


def test_validate_product_image_rejects_extension():
    upload = _make_image(name="foto.gif", content_type="image/gif", fmt="PNG")
    upload.name = "foto.gif"
    with pytest.raises(ValidationError, match="Extensão"):
        validate_product_image(upload)


def test_validate_product_image_rejects_ratio():
    upload = _make_image(width=800, height=400, name="pano.jpg")
    with pytest.raises(ValidationError, match="Proporção"):
        validate_product_image(upload)


def test_validate_product_image_rejects_too_small():
    upload = _make_image(width=200, height=200, name="mini.jpg")
    with pytest.raises(ValidationError, match="pequena"):
        validate_product_image(upload)


def test_prepare_product_image_normalizes_panorama():
    prepared = prepare_product_image(_make_image(width=1600, height=400, name="pano.jpg"))
    assert prepared.name.endswith(".jpg")
    assert prepared.content_type == "image/jpeg"
    assert prepared.size <= PRODUCT_IMAGE_MAX_BYTES
    with Image.open(prepared) as img:
        assert img.size == (PRODUCT_IMAGE_MAX_SIDE, PRODUCT_IMAGE_MAX_SIDE)
        assert img.format == "JPEG"
    validate_product_image(prepared)


def test_prepare_product_image_upsizes_small():
    prepared = prepare_product_image(_make_image(width=200, height=200, name="mini.png", fmt="PNG", content_type="image/png"))
    with Image.open(prepared) as img:
        assert img.size[0] >= PRODUCT_IMAGE_MIN_SIDE
        assert img.size[1] >= PRODUCT_IMAGE_MIN_SIDE
    validate_product_image(prepared)


def test_prepare_product_image_downsizes_large():
    prepared = prepare_product_image(_make_image(width=2400, height=2400, name="grande.webp", fmt="WEBP", content_type="image/webp"))
    with Image.open(prepared) as img:
        assert img.size == (PRODUCT_IMAGE_MAX_SIDE, PRODUCT_IMAGE_MAX_SIDE)
    validate_product_image(prepared)


def test_prepare_product_image_rejects_bad_extension():
    upload = _make_image(name="foto.gif", content_type="image/gif", fmt="PNG")
    upload.name = "foto.gif"
    with pytest.raises(ValidationError, match="Extensão"):
        prepare_product_image(upload)


@pytest.mark.django_db
def test_products_dashboard_upload_image():
    from decimal import Decimal

    from django.contrib.auth.models import User
    from django.test import Client
    from django.urls import reverse

    from apps.catalog.models import Brand, Category
    from apps.products.models import Product, ProductImage

    user = User.objects.create_user(username="imgops", password="x", is_staff=True)
    brand = Brand.objects.create(name="FotoBrand", slug="fotobrand")
    cat = Category.objects.create(name="Fotos", slug="fotos-cat")
    product = Product.objects.create(
        sku="IMG-01",
        brand="FotoBrand",
        brand_ref=brand,
        price=Decimal("10.00"),
        status=Product.Status.DRAFT,
        category=cat,
    )

    client = Client()
    client.force_login(user)
    upload = _make_image(width=1200, height=600, name="nova.png", fmt="PNG", content_type="image/png")
    res = client.post(
        reverse("dashboard:products_edit", args=[product.pk]),
        {
            "sku": "IMG-01",
            "brand_ref": brand.pk,
            "name": "Produto com foto",
            "description": "",
            "price": "10.00",
            "voltage": "",
            "product_kind": "spare_part",
            "status": "draft",
            "category": cat.pk,
            "quantity_available": 1,
            "minimum_alert": 1,
            "images": upload,
        },
    )
    if res.status_code != 302:
        raise AssertionError(
            f"status={res.status_code} form={getattr(res, 'context', None) and res.context['form'].errors} "
            f"images={getattr(res, 'context', None) and res.context.get('image_errors')}"
        )
    saved = ProductImage.objects.get(product=product)
    assert saved.is_primary
    assert saved.image.name.endswith(".jpg")
    with Image.open(saved.image) as img:
        assert img.size == (PRODUCT_IMAGE_MAX_SIDE, PRODUCT_IMAGE_MAX_SIDE)
