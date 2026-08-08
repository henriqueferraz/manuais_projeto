# Generated manually — backfill Brand from Product.brand

from django.db import migrations
from django.utils.text import slugify


def forwards(apps, schema_editor):
    Product = apps.get_model("products", "Product")
    Brand = apps.get_model("catalog", "Brand")

    names = (
        Product.objects.exclude(brand="")
        .values_list("brand", flat=True)
        .distinct()
    )
    name_to_id: dict[str, int] = {}
    for name in names:
        name = (name or "").strip()
        if not name:
            continue
        key = name.casefold()
        if key in name_to_id:
            continue
        slug = slugify(name)[:140] or "marca"
        # avoid slug collisions
        base_slug = slug
        n = 2
        while Brand.objects.filter(slug=slug).exclude(name__iexact=name).exists():
            slug = f"{base_slug}-{n}"[:140]
            n += 1
        obj, _ = Brand.objects.get_or_create(
            name=name,
            defaults={"slug": slug},
        )
        name_to_id[key] = obj.pk

    for product in Product.objects.exclude(brand="").filter(brand_ref_id__isnull=True):
        brand_id = name_to_id.get(product.brand.strip().casefold())
        if brand_id:
            product.brand_ref_id = brand_id
            product.save(update_fields=["brand_ref_id"])


def backwards(apps, schema_editor):
    Product = apps.get_model("products", "Product")
    Product.objects.filter(brand_ref_id__isnull=False).update(brand_ref_id=None)


class Migration(migrations.Migration):
    dependencies = [
        ("products", "0007_brand"),
        ("catalog", "0003_brand"),
    ]

    operations = [
        migrations.RunPython(forwards, backwards),
    ]
