"""Mais fabricantes/categorias para escala de catálogo (F8 / ADR-0008)."""

from __future__ import annotations

from decimal import Decimal

from django.core.management.base import BaseCommand

from apps.catalog.models import Category
from apps.products.models import Product, ProductTranslation, Stock

CATEGORIES = [
    ("Ventiladores de teto", "ventiladores-teto"),
    ("Ventiladores de mesa", "ventiladores-mesa"),
    ("Aspiradores", "aspiradores"),
    ("Liquidificadores", "liquidificadores"),
    ("Ferros de passar", "ferros"),
    ("Peças elétricas", "pecas-eletricas"),
]

BRANDS = (
    "Mondial",
    "Britânia",
    "Electrolux",
    "Consul",
    "Philco",
    "Arno",
    "Samsung",
    "LG",
)


class Command(BaseCommand):
    help = "Popula categorias/marcas adicionais e SKUs de escala (idempotente)."

    def add_arguments(self, parser):
        parser.add_argument("--count", type=int, default=24, help="Quantidade de SKUs a garantir")

    def handle(self, *args, **options):
        count = max(1, int(options["count"]))
        cats = []
        for name, slug in CATEGORIES:
            cat, _ = Category.objects.get_or_create(slug=slug, defaults={"name": name})
            cats.append(cat)
            self.stdout.write(f"categoria: {cat.slug}")

        created = 0
        for i in range(count):
            brand = BRANDS[i % len(BRANDS)]
            cat = cats[i % len(cats)]
            sku = f"SCL-{brand[:3].upper()}-{i + 1:04d}"
            if Product.objects.filter(sku=sku).exists():
                continue
            model = f"MDL-{i + 1:03d}"
            product = Product.objects.create(
                sku=sku,
                brand=brand,
                model_code=model,
                price=Decimal("49.90") + Decimal(i % 20),
                voltage="Bivolt" if i % 2 == 0 else "220V",
                status=Product.Status.PUBLISHED,
                category=cat,
                product_kind=Product.Kind.SPARE_PART if i % 3 == 0 else Product.Kind.FINISHED_GOOD,
            )
            ProductTranslation.objects.create(
                product=product,
                locale="pt-BR",
                name=f"{brand} {model}",
                description=f"Peça/escala seed {sku}",
            )
            # T-P.5: conteúdo EN/ES além da estrutura i18n
            ProductTranslation.objects.get_or_create(
                product=product,
                locale="en",
                defaults={
                    "name": f"{brand} {model} spare part",
                    "description": f"Scale catalog seed part {sku} (EN).",
                },
            )
            ProductTranslation.objects.get_or_create(
                product=product,
                locale="es",
                defaults={
                    "name": f"{brand} {model} repuesto",
                    "description": f"Pieza seed de escala {sku} (ES).",
                },
            )
            Stock.objects.create(
                product=product, quantity_available=10 + (i % 8), quantity_reserved=0
            )
            created += 1
            self.stdout.write(self.style.SUCCESS(f"SKU {sku}"))

        self.stdout.write(self.style.SUCCESS(f"Criados: {created} (categorias={len(cats)})"))
        self.stdout.write(
            "Índices: Product(status,brand/voltage/model/sku) — ver ADR-0008 revisão T-P.5."
        )
