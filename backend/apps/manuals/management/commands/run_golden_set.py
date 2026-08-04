"""Golden set inicial de extração (T-3.4) — regressão local; CI completo na F6."""

from __future__ import annotations

import json
from pathlib import Path

from django.core.management.base import BaseCommand, CommandError

from apps.manuals.schemas import ExtractedProduct
from apps.manuals.services.sanitize import sanitize_manual_text
from apps.manuals.services.structure import structure_manual_text

GOLDEN_DIR = Path(__file__).resolve().parents[2] / "golden_set"


class Command(BaseCommand):
    help = "Roda regressão do golden set de extração (mock LLM)."

    def add_arguments(self, parser):
        parser.add_argument(
            "--min-score",
            type=float,
            default=0.66,
            help="Fração mínima de casos OK (default 0.66 ≈ 2/3).",
        )

    def handle(self, *args, **options):
        cases_dir = GOLDEN_DIR / "cases"
        if not cases_dir.exists():
            raise CommandError(f"Golden set não encontrado: {cases_dir}")

        cases = sorted(cases_dir.glob("*.json"))
        if not cases:
            raise CommandError("Nenhum caso no golden set.")

        passed = 0
        failed_details: list[str] = []

        for case_path in cases:
            case = json.loads(case_path.read_text(encoding="utf-8"))
            text_path = GOLDEN_DIR / "fixtures" / case["fixture"]
            text = text_path.read_text(encoding="utf-8")
            cleaned = sanitize_manual_text(text)
            result = structure_manual_text(
                cleaned,
                manufacturer_hint=case.get("manufacturer_hint", ""),
                filename=case.get("filename", case_path.name),
            )
            expected = ExtractedProduct.model_validate(case["expected"])
            ok, reasons = _compare(result.product, expected, case.get("require", {}))
            if ok:
                passed += 1
                self.stdout.write(self.style.SUCCESS(f"OK  {case_path.name}"))
            else:
                failed_details.append(f"{case_path.name}: " + "; ".join(reasons))
                self.stdout.write(self.style.ERROR(f"FAIL {case_path.name}: {reasons}"))

        total = len(cases)
        score = passed / total
        self.stdout.write(f"Score: {passed}/{total} ({score:.0%})")
        min_score = float(options["min_score"])
        if score < min_score:
            raise CommandError(
                f"Golden set abaixo do mínimo ({score:.0%} < {min_score:.0%}). "
                + " | ".join(failed_details)
            )
        self.stdout.write(self.style.SUCCESS("Golden set passou no critério mínimo."))


def _compare(
    got: ExtractedProduct,
    expected: ExtractedProduct,
    require: dict,
) -> tuple[bool, list[str]]:
    reasons: list[str] = []
    fields = require.get("fields") or ["brand", "model_code"]
    for field in fields:
        g = getattr(got, field, None)
        e = getattr(expected, field, None)
        if field in ("brand", "model_code", "voltage", "name"):
            if str(g or "").strip().lower() != str(e or "").strip().lower():
                # model_code: aceita contenção parcial
                if field == "model_code" and e and str(e).upper() in str(g or "").upper():
                    continue
                if field == "brand" and e and str(e).lower() in str(g or "").lower():
                    continue
                reasons.append(f"{field}: got={g!r} expected={e!r}")
        elif field == "power_w":
            if e is not None and g is not None and abs(float(g) - float(e)) > 1.0:
                reasons.append(f"power_w: got={g} expected={e}")
            elif e is not None and g is None:
                reasons.append(f"power_w missing (expected {e})")
    return (len(reasons) == 0, reasons)
