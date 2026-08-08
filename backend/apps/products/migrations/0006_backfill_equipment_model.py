# Generated manually — backfill EquipmentModel from Product.model_code

from django.db import migrations
from django.utils.text import slugify


def forwards(apps, schema_editor):
    Product = apps.get_model("products", "Product")
    EquipmentModel = apps.get_model("catalog", "EquipmentModel")

    pairs = (
        Product.objects.exclude(model_code="")
        .values_list("model_code", "brand")
        .distinct()
    )
    code_to_id: dict[str, int] = {}
    for code, brand in pairs:
        code = (code or "").strip()
        if not code:
            continue
        if code in code_to_id:
            continue
        brand = (brand or "").strip()
        base = slugify(f"{brand}-{code}") or slugify(code) or "modelo"
        slug = base[:160]
        obj, _ = EquipmentModel.objects.get_or_create(
            code=code,
            defaults={"brand": brand, "name": "", "slug": slug},
        )
        # ensure unique slug if collision
        if obj.slug != slug and not EquipmentModel.objects.filter(slug=slug).exclude(pk=obj.pk).exists():
            pass
        code_to_id[code] = obj.pk

    for product in Product.objects.exclude(model_code="").filter(equipment_model_id__isnull=True):
        em_id = code_to_id.get(product.model_code.strip())
        if em_id:
            product.equipment_model_id = em_id
            product.save(update_fields=["equipment_model_id"])


def backwards(apps, schema_editor):
    Product = apps.get_model("products", "Product")
    Product.objects.filter(equipment_model_id__isnull=False).update(equipment_model_id=None)


class Migration(migrations.Migration):
    dependencies = [
        ("products", "0005_equipment_model"),
        ("catalog", "0002_equipment_model"),
    ]

    operations = [
        migrations.RunPython(forwards, backwards),
    ]
