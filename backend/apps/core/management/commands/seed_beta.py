"""Ambiente mínimo para sessões de beta humana (T-P.1 / pós-F8).

Cria (idempotente):
- grupos RBAC
- staff + tester beta (senhas só para DEBUG local)
- produto acabado VTE-02 + peça CAP-35 com estoque
- manual indexado com texto golden (RAG/diagnóstico)

Uso:
  python manage.py seed_beta
  python manage.py seed_beta --password 'segredo-local'
"""

from __future__ import annotations

from decimal import Decimal
from pathlib import Path

from django.conf import settings
from django.contrib.auth import get_user_model
from django.contrib.auth.models import Group
from django.core.files.base import ContentFile
from django.core.management import call_command
from django.core.management.base import BaseCommand, CommandError

from apps.ai.models import ManualChunk
from apps.ai.services.retrieval import index_manual
from apps.catalog.models import Category
from apps.compatibility.models import Compatibility
from apps.manuals.models import Manual
from apps.products.models import Product, ProductTranslation, Stock

User = get_user_model()

DEFAULT_STAFF = "beta.staff@techparts.local"
DEFAULT_TESTER = "beta.tester@techparts.local"
DEFAULT_PASSWORD = "beta-local-only"

FIXTURE_PATH = (
    Path(settings.BASE_DIR) / "apps" / "ai" / "golden_set" / "fixtures" / "vte02_capacitor.txt"
)

MANUAL_FALLBACK = """
# Instalação
Página 3
Antes de instalar o ventilador Mondial VTE-02, desligue a energia no disjuntor.

# Manutenção
Página 12
A cada 6 meses limpe as pás com pano seco.
O capacitor de partida do modelo VTE-02 é de 3.5 uF e fica no compartimento superior.
Código da peça: CAP-35.

# Diagnóstico
Página 14
Quando o ventilador VTE-02 faz barulho e não gira, verifique o capacitor de partida.

# Tabela de peças
Página 18
| Código | Peça | Compatível |
| CAP-35 | Capacitor 3.5uF | VTE-02 |
| PAL-01 | Pá plástica | VTE-02 |
""".strip()


class Command(BaseCommand):
    help = "Prepara catálogo VTE-02 + usuários para beta humana (T-P.1)."

    def add_arguments(self, parser):
        parser.add_argument(
            "--password",
            default=DEFAULT_PASSWORD,
            help="Senha dos usuários beta (somente DEBUG/local).",
        )
        parser.add_argument(
            "--force",
            action="store_true",
            help="Permite rodar com DEBUG=False (não use em produção).",
        )
        parser.add_argument(
            "--reindex",
            action="store_true",
            help="Reindexa o manual mesmo se já houver chunks.",
        )

    def handle(self, *args, **options):
        if not settings.DEBUG and not options["force"]:
            raise CommandError(
                "seed_beta recusado com DEBUG=False. Use --force só em staging controlado."
            )

        password = options["password"]
        call_command("bootstrap_rbac")

        staff = self._ensure_user(
            DEFAULT_STAFF,
            password=password,
            is_staff=True,
            is_superuser=True,
            groups=("admin", "revisao_catalogo", "suporte"),
        )
        tester = self._ensure_user(
            DEFAULT_TESTER,
            password=password,
            is_staff=False,
            is_superuser=False,
            groups=(),
        )

        category, _ = Category.objects.get_or_create(
            slug="ventiladores-teto",
            defaults={"name": "Ventiladores de teto"},
        )

        equipment = self._ensure_product(
            sku="VTE-02",
            brand="Mondial",
            model_code="VTE-02",
            kind=Product.Kind.FINISHED_GOOD,
            price=Decimal("289.90"),
            name="Ventilador de teto Mondial VTE-02",
            description="Equipamento de referência do beta (manual indexado).",
            category=category,
            qty=5,
        )
        part = self._ensure_product(
            sku="CAP-35",
            brand="Mondial",
            model_code="CAP-35",
            kind=Product.Kind.SPARE_PART,
            price=Decimal("39.90"),
            name="Capacitor de partida 3.5uF CAP-35",
            description="Peça compatível com Mondial VTE-02 — fluxo de compra do beta.",
            category=category,
            qty=25,
        )

        Compatibility.objects.get_or_create(
            equipment_brand=equipment.brand,
            equipment_model=equipment.model_code,
            part_product=part,
            defaults={"notes": "Capacitor de partida oficial VTE-02 (beta)."},
        )

        manual, created_manual = self._ensure_manual(equipment, uploaded_by=staff)
        chunks = ManualChunk.objects.filter(manual=manual).count()
        if created_manual or options["reindex"] or chunks == 0:
            text = self._manual_text()
            indexed = index_manual(manual.pk, text=text)
            self.stdout.write(self.style.SUCCESS(f"Manual indexado: {indexed} chunks"))
        else:
            self.stdout.write(f"Manual já indexado ({chunks} chunks); use --reindex se precisar.")

        self.stdout.write("")
        self.stdout.write(self.style.SUCCESS("Beta seed pronto."))
        self.stdout.write(f"  Staff:  {staff.username} / {password}")
        self.stdout.write(f"  Tester: {tester.username} / {password}")
        self.stdout.write("  Catálogo: VTE-02 (equipamento) · CAP-35 (peça)")
        self.stdout.write("  Chat:    /assistente/chat/  (pergunte pelo capacitor VTE-02)")
        self.stdout.write("  Script:  docs/beta-script.md")

    def _ensure_user(
        self,
        username: str,
        *,
        password: str,
        is_staff: bool,
        is_superuser: bool,
        groups: tuple[str, ...],
    ):
        user, created = User.objects.get_or_create(
            username=username,
            defaults={
                "email": username,
                "is_staff": is_staff,
                "is_superuser": is_superuser,
            },
        )
        changed = False
        if user.email != username:
            user.email = username
            changed = True
        if user.is_staff != is_staff:
            user.is_staff = is_staff
            changed = True
        if user.is_superuser != is_superuser:
            user.is_superuser = is_superuser
            changed = True
        if created or changed:
            user.set_password(password)
            user.save()
            label = "criado" if created else "atualizado"
            self.stdout.write(self.style.SUCCESS(f"Usuário {label}: {username}"))
        else:
            user.set_password(password)
            user.save(update_fields=["password"])
            self.stdout.write(f"Usuário já existe: {username} (senha sincronizada)")

        for name in groups:
            group = Group.objects.get(name=name)
            user.groups.add(group)
        return user

    def _ensure_product(
        self,
        *,
        sku: str,
        brand: str,
        model_code: str,
        kind: str,
        price: Decimal,
        name: str,
        description: str,
        category: Category,
        qty: int,
    ) -> Product:
        product, created = Product.objects.get_or_create(
            sku=sku,
            defaults={
                "brand": brand,
                "model_code": model_code,
                "price": price,
                "voltage": "Bivolt",
                "status": Product.Status.PUBLISHED,
                "category": category,
                "product_kind": kind,
            },
        )
        if not created:
            product.brand = brand
            product.model_code = model_code
            product.price = price
            product.status = Product.Status.PUBLISHED
            product.category = category
            product.product_kind = kind
            product.save()
            self.stdout.write(f"Produto já existe: {sku}")
        else:
            self.stdout.write(self.style.SUCCESS(f"Produto criado: {sku}"))

        ProductTranslation.objects.update_or_create(
            product=product,
            locale="pt-BR",
            defaults={"name": name, "description": description},
        )
        Stock.objects.update_or_create(
            product=product,
            defaults={"quantity_available": qty, "quantity_reserved": 0, "minimum_alert": 2},
        )
        return product

    def _ensure_manual(self, equipment: Product, *, uploaded_by) -> tuple[Manual, bool]:
        existing = Manual.objects.filter(
            manufacturer="Mondial",
            linked_product=equipment,
            original_filename="Manual-VTE-02-beta.pdf",
        ).first()
        if existing:
            return existing, False

        content = b"%PDF-1.4\n% TechParts beta VTE-02\n%%EOF\n"
        manual = Manual(
            original_filename="Manual-VTE-02-beta.pdf",
            mime_type="application/pdf",
            manufacturer="Mondial",
            linked_product=equipment,
            scan_status=Manual.ScanStatus.SKIPPED,
            uploaded_by=uploaded_by,
        )
        manual.file.save("Manual-VTE-02-beta.pdf", ContentFile(content), save=False)
        manual.compute_and_set_sha256(content)
        manual.save()
        self.stdout.write(self.style.SUCCESS(f"Manual criado: {manual.original_filename}"))
        return manual, True

    def _manual_text(self) -> str:
        if FIXTURE_PATH.is_file():
            base = FIXTURE_PATH.read_text(encoding="utf-8").strip()
            extra = (
                "\n\n# Diagnóstico\nPágina 14\n"
                "Quando o ventilador VTE-02 faz barulho e não gira, "
                "verifique o capacitor de partida.\n"
            )
            return f"{base}{extra}"
        return MANUAL_FALLBACK
