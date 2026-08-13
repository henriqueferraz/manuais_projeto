"""Testes F4a — catálogo, estoque, carrinho, compatibilidade."""

from __future__ import annotations

import pytest
from django.contrib.auth.models import AnonymousUser, User
from django.contrib.sessions.middleware import SessionMiddleware
from django.core.exceptions import ValidationError
from django.urls import reverse

from apps.cart.services import add_to_cart
from apps.catalog.models import Category
from apps.catalog.services import filter_catalog
from apps.compatibility.models import Compatibility
from apps.products.models import Product, ProductTranslation, Stock


@pytest.fixture
def category(db):
    return Category.objects.create(name="Ventiladores", slug="ventiladores")


@pytest.mark.django_db
def test_category_name_always_initial_cap():
    cat = Category.objects.create(name="ventilador de teto", slug="ventilador-de-teto")
    assert cat.name == "Ventilador de teto"
    cat.name = "peças elétricas"
    cat.save()
    cat.refresh_from_db()
    assert cat.name == "Peças elétricas"


@pytest.fixture
def published_product(category):
    p = Product.objects.create(
        sku="MON-VTE02",
        brand="Mondial",
        model_code="VTE-02",
        price="199.90",
        voltage="Bivolt",
        status=Product.Status.PUBLISHED,
        category=category,
        product_kind=Product.Kind.FINISHED_GOOD,
        specs={"blade_count": 3},
    )
    ProductTranslation.objects.create(
        product=p, locale="pt-BR", name="Ventilador de Teto VTE-02", description="Manual Mondial"
    )
    Stock.objects.create(product=p, quantity_available=5, quantity_reserved=0, minimum_alert=1)
    return p


@pytest.fixture
def spare_part(category):
    p = Product.objects.create(
        sku="PEC-HELICE",
        brand="Mondial",
        model_code="HELICE-VTE",
        price="49.90",
        status=Product.Status.PUBLISHED,
        category=category,
        product_kind=Product.Kind.SPARE_PART,
    )
    ProductTranslation.objects.create(product=p, locale="pt-BR", name="Hélice VTE")
    Stock.objects.create(product=p, quantity_available=10, quantity_reserved=0)
    Compatibility.objects.create(
        equipment_brand="Mondial",
        equipment_model="VTE-02",
        part_product=p,
    )
    return p


@pytest.mark.django_db
def test_primary_image_skips_empty_file(published_product):
    from django.core.files.base import ContentFile

    from apps.products.models import ProductImage

    empty = ProductImage.objects.create(
        product=published_product,
        alt_text="vazio",
        sort_order=0,
        is_primary=True,
    )
    assert not empty.image
    good = ProductImage(
        product=published_product,
        alt_text="ok",
        sort_order=1,
        is_primary=False,
    )
    good.image.save("ok.png", ContentFile(b"\x89PNG\r\n\x1a\n"), save=True)
    assert published_product.primary_image.pk == good.pk


@pytest.mark.django_db
def test_stock_reserve_and_release(published_product):
    Stock.reserve(published_product.id, 2)
    published_product.stock.refresh_from_db()
    assert published_product.stock.quantity_reserved == 2
    assert published_product.stock.sellable == 3

    Stock.release(published_product.id, 1)
    published_product.stock.refresh_from_db()
    assert published_product.stock.quantity_reserved == 1


@pytest.mark.django_db
def test_stock_reserve_oversell_raises(published_product):
    with pytest.raises(ValidationError):
        Stock.reserve(published_product.id, 99)


@pytest.mark.django_db
def test_filter_catalog_by_voltage_and_q(published_product):
    qs = filter_catalog(voltage="Bivolt", q="VTE")
    assert published_product in qs
    assert filter_catalog(voltage="110V").count() == 0


@pytest.mark.django_db
def test_filter_catalog_by_secondary_category(published_product):
    spare = Category.objects.create(name="Peça de reposição", slug="peca-de-reposicao")
    moveis = Category.objects.create(name="Móveis", slug="moveis")
    published_product.categories.set([spare, moveis])
    published_product.category = spare
    published_product.save(update_fields=["category"])

    by_moveis = filter_catalog(category="moveis")
    assert published_product in by_moveis
    by_name = filter_catalog(category="Móveis")
    assert published_product in by_name
    assert published_product not in filter_catalog(category="outra-categoria")


@pytest.mark.django_db
def test_filter_catalog_sort_by_name_and_price(category):
    # Marca "Zebra" mas nome começa com A — deve vir primeiro no A–Z pelo nome.
    alpha = Product.objects.create(
        sku="SORT-Z",
        brand="Zebra",
        model_code="Z-90",
        price="990.00",
        status=Product.Status.PUBLISHED,
        category=category,
        product_kind=Product.Kind.FINISHED_GOOD,
    )
    ProductTranslation.objects.create(
        product=alpha, locale="pt-BR", name="Alpha Peça Premium", description=""
    )
    # Marca "Acme" mas nome começa com Z — deve vir depois no A–Z.
    zulu = Product.objects.create(
        sku="SORT-A",
        brand="Acme",
        model_code="A-10",
        price="10.00",
        status=Product.Status.PUBLISHED,
        category=category,
        product_kind=Product.Kind.FINISHED_GOOD,
    )
    ProductTranslation.objects.create(
        product=zulu, locale="pt-BR", name="Zulu Peça Básica", description=""
    )

    by_name = list(filter_catalog(sort="name_asc").values_list("sku", flat=True))
    assert by_name.index(alpha.sku) < by_name.index(zulu.sku)
    by_name_desc = list(filter_catalog(sort="name_desc").values_list("sku", flat=True))
    assert by_name_desc.index(zulu.sku) < by_name_desc.index(alpha.sku)
    by_price_asc = list(filter_catalog(sort="price_asc").values_list("sku", flat=True))
    assert by_price_asc.index(zulu.sku) < by_price_asc.index(alpha.sku)
    by_price_desc = list(filter_catalog(sort="price_desc").values_list("sku", flat=True))
    assert by_price_desc.index(alpha.sku) < by_price_desc.index(zulu.sku)


@pytest.mark.django_db
def test_catalog_list_and_detail(client, published_product):
    r = client.get(reverse("catalog:list"))
    assert r.status_code == 200
    assert b"VTE-02" in r.content or b"Ventilador" in r.content
    assert b"Ordenar por" in r.content
    assert b'name="sort"' in r.content

    r_sorted = client.get(reverse("catalog:list"), {"sort": "price_desc"})
    assert r_sorted.status_code == 200
    assert r_sorted.context["params"]["sort"] == "price_desc"

    r2 = client.get(reverse("catalog:detail", kwargs={"slug": published_product.slug}))
    assert r2.status_code == 200
    assert b"Adicionar ao carrinho" in r2.content


@pytest.mark.django_db
def test_product_manual_download_and_gallery_excludes_cover(client, published_product, settings):
    from django.core.files.base import ContentFile

    from apps.manuals.models import Manual
    from apps.products.image_validation import gallery_image_count, gallery_images_queryset
    from apps.products.models import ProductImage

    settings.MANUAL_AV_STUB_OK = True
    manual = Manual.objects.create(
        original_filename="vte-manual.pdf",
        mime_type="application/pdf",
        sha256="c" * 64,
        size_bytes=32,
        scan_status=Manual.ScanStatus.CLEAN,
        linked_product=published_product,
    )
    manual.file.save("vte-manual.pdf", ContentFile(b"%PDF-1.4\n%%EOF\n"), save=True)
    published_product.manual = manual
    published_product.save(update_fields=["manual", "updated_at"])

    ProductImage.objects.create(
        product=published_product,
        alt_text=f"Capa do manual — {published_product.sku}",
        sort_order=0,
        is_primary=True,
        image=ContentFile(b"not-a-real-image", name="capa.jpg"),
    )
    # Contagem de vitrine ignora capa
    assert gallery_image_count(published_product) == 0
    assert gallery_images_queryset(published_product).count() == 0

    detail = client.get(reverse("catalog:detail", kwargs={"slug": published_product.slug}))
    assert detail.status_code == 200
    assert b"Baixar manual PDF" in detail.content
    assert b"capa.jpg" not in detail.content

    dl = client.get(reverse("catalog:manual_download", kwargs={"slug": published_product.slug}))
    assert dl.status_code == 200
    assert dl["Content-Type"].startswith("application/pdf")
    assert "attachment" in dl.get("Content-Disposition", "")


@pytest.mark.django_db
def test_catalog_htmx_partial(client, published_product):
    r = client.get(reverse("catalog:list"), HTTP_HX_REQUEST="true")
    assert r.status_code == 200
    assert b"tp-product-card" in r.content


@pytest.mark.django_db
def test_cart_add_reserves_stock(client, published_product):
    session = client.session
    session.save()
    r = client.post(
        reverse("cart:add"),
        {"product_id": published_product.pk, "quantity": 2},
    )
    assert r.status_code in (200, 302)
    published_product.stock.refresh_from_db()
    assert published_product.stock.quantity_reserved == 2

    r2 = client.get(reverse("cart:detail"))
    assert r2.status_code == 200
    assert b"MON-VTE02" in r2.content or b"VTE-02" in r2.content


@pytest.mark.django_db
def test_cart_add_without_stock_errors(rf, published_product):
    published_product.stock.quantity_available = 0
    published_product.stock.save()
    request = rf.post("/carrinho/adicionar/")
    middleware = SessionMiddleware(lambda r: None)
    middleware.process_request(request)
    request.session.save()
    request.user = AnonymousUser()
    with pytest.raises(ValidationError):
        add_to_cart(request, published_product, 1)


@pytest.mark.django_db
def test_compatibility_checker(client, spare_part):
    r = client.post(
        reverse("compatibility:checker"),
        {"brand": "Mondial", "model": "VTE-02"},
    )
    assert r.status_code == 200
    assert b"HELICE" in r.content or b"H" in r.content


@pytest.mark.django_db
def test_ops_requires_staff(client):
    r = client.get(reverse("dashboard:products"))
    assert r.status_code in (302, 301)


@pytest.mark.django_db
def test_ops_staff_can_create(client, category):
    from apps.catalog.models import Brand, EquipmentModel

    user = User.objects.create_user(username="ops", password="x", is_staff=True)
    client.force_login(user)
    brand = Brand.objects.create(name="Mondial", slug="mondial")
    model = EquipmentModel.objects.create(code="X1", brand="Mondial", slug="mondial-x1")
    r = client.post(
        reverse("dashboard:products_create"),
        {
            "sku": "NEW-001",
            "brand_ref": brand.pk,
            "equipment_model": model.pk,
            "name": "Peça teste",
            "description": "",
            "price": "10.00",
            "voltage": "220V",
            "product_kind": "spare_part",
            "status": "draft",
            "categories": category.pk,
            "quantity_available": 3,
            "minimum_alert": 1,
        },
    )
    assert r.status_code == 302
    product = Product.objects.get(sku="NEW-001")
    assert product.status == "draft"
    assert product.brand == "Mondial"
    assert product.model_code == "X1"
    assert product.category_id == category.pk
    assert list(product.categories.values_list("pk", flat=True)) == [category.pk]
    assert Stock.objects.filter(product__sku="NEW-001", quantity_available=3).exists()


@pytest.mark.django_db
def test_legacy_ops_url_still_serves_dashboard(client):
    user = User.objects.create_user(username="ops2", password="x", is_staff=True)
    client.force_login(user)
    r = client.get(reverse("compatibility:ops_list"))
    assert r.status_code == 200
    assert b"Estoque e produtos" in r.content


@pytest.mark.django_db
def test_remove_cart_releases_reservation(client, published_product):
    client.post(reverse("cart:add"), {"product_id": published_product.pk, "quantity": 1})
    published_product.stock.refresh_from_db()
    assert published_product.stock.quantity_reserved == 1
    client.post(reverse("cart:remove"), {"product_id": published_product.pk})
    published_product.stock.refresh_from_db()
    assert published_product.stock.quantity_reserved == 0
