from django.db import migrations


def capitalize_category_names(apps, schema_editor):
    import re

    Category = apps.get_model("catalog", "Category")
    multi_space = re.compile(r"\s+")
    for cat in Category.objects.all().iterator():
        name = multi_space.sub(" ", (cat.name or "").strip())
        if not name:
            continue
        new_name = name
        for idx, char in enumerate(name):
            if char.isalpha():
                new_name = name[:idx] + char.upper() + name[idx + 1 :]
                break
        if new_name != cat.name:
            cat.name = new_name[:120]
            cat.save(update_fields=["name"])


def noop_reverse(apps, schema_editor):
    pass


class Migration(migrations.Migration):
    dependencies = [
        ("catalog", "0003_brand"),
    ]

    operations = [
        migrations.RunPython(capitalize_category_names, noop_reverse),
    ]
