"""Command: golden set RAG (perguntas → trechos esperados)."""

from __future__ import annotations

import json
from pathlib import Path

from django.core.files.base import ContentFile
from django.core.management.base import BaseCommand, CommandError

from apps.ai.services.retrieval import index_manual, retrieve
from apps.manuals.models import Manual
from apps.products.models import Product

GOLDEN_DIR = Path(__file__).resolve().parents[2] / "golden_set"


class Command(BaseCommand):
    help = "Regressão golden set de retrieval RAG (mock embeddings)."

    def add_arguments(self, parser):
        parser.add_argument(
            "--min-score",
            type=float,
            default=None,
            help="Fração mínima de casos OK (default settings.RAG_GOLDEN_MIN_SCORE).",
        )

    def handle(self, *args, **options):
        from django.conf import settings
        from django.core.management import call_command

        # Em SQLite :memory: (CI/test) a DB chega vazia — aplica migrations.
        call_command("migrate", run_syncdb=True, verbosity=0)

        min_score = options["min_score"]
        if min_score is None:
            min_score = float(getattr(settings, "RAG_GOLDEN_MIN_SCORE", 0.66))

        cases_dir = GOLDEN_DIR / "cases"
        fixtures_dir = GOLDEN_DIR / "fixtures"
        if not cases_dir.exists():
            raise CommandError(f"Diretório de casos ausente: {cases_dir}")

        cases = sorted(cases_dir.glob("*.json"))
        if not cases:
            raise CommandError("Nenhum caso golden RAG encontrado.")

        ok = 0
        for case_path in cases:
            payload = json.loads(case_path.read_text(encoding="utf-8"))
            fixture_name = payload["fixture"]
            fixture_path = fixtures_dir / fixture_name
            text = fixture_path.read_text(encoding="utf-8")
            question = payload["question"]
            expect_any = [s.lower() for s in payload.get("expect_any", [])]

            product = Product.objects.create(
                sku=f"GOLDEN-{case_path.stem}"[:64],
                brand=payload.get("brand", "Test"),
                model_code=payload.get("model", "X"),
                status=Product.Status.PUBLISHED,
                price=1,
            )
            manual = Manual(
                original_filename=f"{case_path.stem}.pdf",
                mime_type="application/pdf",
                manufacturer=product.brand,
                linked_product=product,
                scan_status=Manual.ScanStatus.SKIPPED,
            )
            manual.file.save(
                f"{case_path.stem}.pdf",
                ContentFile(b"%PDF-1.4\n%%EOF\n"),
                save=False,
            )
            manual.compute_and_set_sha256(b"%PDF-1.4\n%%EOF\n")
            manual.save()
            index_manual(manual.pk, text=text)
            hits = retrieve(question, product_id=product.pk)
            joined = " ".join(h.chunk.content.lower() for h in hits)
            passed = bool(hits) and any(tok in joined for tok in expect_any)
            if passed:
                ok += 1
                self.stdout.write(self.style.SUCCESS(f"OK  {case_path.name}"))
            else:
                self.stdout.write(self.style.ERROR(f"FAIL {case_path.name}"))
                self.stdout.write(f"  got: {joined[:200]!r}")

        total = len(cases)
        ratio = ok / total if total else 0.0
        self.stdout.write(f"Score: {ok}/{total} ({ratio:.0%})")
        if ratio + 1e-9 < min_score:
            raise CommandError(f"Golden RAG abaixo do mínimo ({ratio:.0%} < {min_score:.0%}).")
        self.stdout.write(self.style.SUCCESS("Golden RAG passou no critério mínimo."))
