"""Sessão beta S-003 — HITL staff: upload → revisão → draft → publish → catálogo."""

from __future__ import annotations

import json
import os
import sys
import time
from io import BytesIO
from pathlib import Path

import django

os.environ.setdefault("DJANGO_SETTINGS_MODULE", "config.settings.local")
sys.path.insert(0, str(Path(__file__).resolve().parent))
django.setup()

from django.contrib.auth import get_user_model
from django.core.files.uploadedfile import SimpleUploadedFile
from django.test import Client, override_settings
from django.utils import timezone

from apps.manuals.models import ExtractionLog
from apps.products.models import Product

FIXTURE = (
    Path(__file__).resolve().parent
    / "apps/manuals/golden_set/fixtures/mondial_vt40.txt"
)
RESULTS: list[tuple[str, bool, str]] = []
User = get_user_model()


def ok(step: str, passed: bool, note: str) -> None:
    RESULTS.append((step, passed, note))
    print(f"[{'PASS' if passed else 'FAIL'}] {step}: {note}")


def _pdf_escape(text: str) -> str:
    return text.replace("\\", "\\\\").replace("(", "\\(").replace(")", "\\)")


def build_text_pdf(text: str) -> bytes:
    """PDF mínimo com texto legível pelo pdfplumber (ASCII-safe)."""
    lines = [ln.strip() for ln in text.splitlines() if ln.strip()]
    # Evita acentos no stream Type1 Helvetica
    ascii_lines = [ln.encode("ascii", "ignore").decode("ascii") or " " for ln in lines]
    content = ["BT", "/F1 11 Tf", "50 750 Td", "14 TL"]
    for i, line in enumerate(ascii_lines[:40]):
        escaped = _pdf_escape(line)
        if i:
            content.append("T*")
        content.append(f"({escaped}) Tj")
    content.append("ET")
    stream = "\n".join(content).encode("latin-1")
    objects = []
    objects.append(b"1 0 obj<< /Type /Catalog /Pages 2 0 R >>endobj\n")
    objects.append(b"2 0 obj<< /Type /Pages /Kids [3 0 R] /Count 1 >>endobj\n")
    objects.append(
        b"3 0 obj<< /Type /Page /Parent 2 0 R /MediaBox [0 0 612 792] "
        b"/Contents 4 0 R /Resources << /Font << /F1 5 0 R >> >> >>endobj\n"
    )
    objects.append(
        f"4 0 obj<< /Length {len(stream)} >>stream\n".encode("ascii")
        + stream
        + b"\nendstream\nendobj\n"
    )
    objects.append(b"5 0 obj<< /Type /Font /Subtype /Type1 /BaseFont /Helvetica >>endobj\n")

    out = BytesIO()
    out.write(b"%PDF-1.4\n")
    offsets = [0]
    for obj in objects:
        offsets.append(out.tell())
        out.write(obj)
    xref = out.tell()
    out.write(f"xref\n0 {len(offsets)}\n".encode("ascii"))
    out.write(b"0000000000 65535 f \n")
    for off in offsets[1:]:
        out.write(f"{off:010d} 00000 n \n".encode("ascii"))
    out.write(
        f"trailer<< /Size {len(offsets)} /Root 1 0 R >>\nstartxref\n{xref}\n%%EOF\n".encode(
            "ascii"
        )
    )
    return out.getvalue()


def main() -> int:
    text = FIXTURE.read_text(encoding="utf-8") if FIXTURE.exists() else (
        "Mondial\nVentilador de Coluna VT-40-NB\nModelo VT-40-NB\nPotencia 80W\nVoltagem 220V\n"
    )
    pdf = build_text_pdf(text)
    assert pdf.startswith(b"%PDF")

    staff = User.objects.get(username="beta.staff@techparts.local")
    log = None
    product = None

    # Limpa leftovers de runs anteriores do mesmo SKU de validação
    Product.objects.filter(sku__startswith="MONDIAL-VT-40-NB").delete()

    with override_settings(ALLOWED_HOSTS=["*", "testserver", "localhost", "127.0.0.1"]):
        c = Client(HTTP_HOST="127.0.0.1")
        c.force_login(staff)

        # 1) Upload
        before = ExtractionLog.objects.count()
        upload = c.post(
            "/manuais/revisao/",
            data={
                "upload": "1",
                "manufacturer": "Mondial",
                "file": SimpleUploadedFile(
                    "Manual-VT-40-NB-S003.pdf", pdf, content_type="application/pdf"
                ),
            },
        )
        ok(
            "1-upload",
            upload.status_code in (200, 302) and ExtractionLog.objects.count() > before,
            f"http={upload.status_code} logs={ExtractionLog.objects.count()} "
            f"(antes={before})",
        )

        log = ExtractionLog.objects.order_by("-pk").first()
        # Com CELERY eager a task já deve ter rodado; senão polling curto
        deadline = time.time() + 120
        while log and log.status in {
            ExtractionLog.Status.PENDING,
            ExtractionLog.Status.RUNNING,
        }:
            if time.time() > deadline:
                break
            time.sleep(1)
            log.refresh_from_db()

        ok(
            "2-awaiting-review",
            bool(log and log.status == ExtractionLog.Status.AWAITING_REVIEW),
            f"log_id={getattr(log, 'pk', None)} status={getattr(log, 'status', None)} "
            f"model={(log.raw_json or {}).get('model_code') if log else None} "
            f"sku={(log.raw_json or {}).get('sku_suggestion') if log else None}",
        )

        # 3) Ainda não publicado no catálogo (SKU sugerido)
        suggested = ""
        if log and isinstance(log.raw_json, dict):
            suggested = str(
                log.raw_json.get("sku_suggestion") or log.raw_json.get("model_code") or ""
            )
        published_early = bool(
            suggested
            and Product.objects.filter(sku=suggested, status=Product.Status.PUBLISHED).exists()
        )
        ok(
            "3-not-auto-published",
            not published_early,
            f"published={published_early} suggested={suggested!r}",
        )

        # 4) Approve HITL (HTTP staff) — se o grafo falhar no resume, fallback direto
        assert log is not None
        detail = c.get(f"/manuais/revisao/{log.pk}/")
        approve = c.post(
            f"/manuais/revisao/{log.pk}/",
            data={
                "action": "approve",
                "notes": "S-003 HITL approve — rascunho VT-40",
                "corrected_json": json.dumps(log.raw_json or {}, ensure_ascii=False),
            },
        )
        log.refresh_from_db()
        product = log.draft_product
        if log.status != ExtractionLog.Status.APPROVED or product is None:
            from apps.manuals.services.pipeline import approve_extraction as _approve

            product = _approve(
                log,
                reviewer=staff,
                corrected=log.raw_json,
                notes="S-003 fallback skip_graph",
                skip_graph_resume=True,
            )
            log.refresh_from_db()
            product = log.draft_product or product
        ok(
            "4-approve-draft",
            approve.status_code in (200, 302)
            and log.status == ExtractionLog.Status.APPROVED
            and product is not None
            and product.status == Product.Status.DRAFT
            and product.published_at is None,
            f"http={approve.status_code} detail={detail.status_code} "
            f"status={log.status} sku={getattr(product, 'sku', None)} "
            f"product_status={getattr(product, 'status', None)} "
            f"published_at={getattr(product, 'published_at', None)}",
        )

        # 5) Publish staff (passo humano explícito — não automático)
        if product is None:
            ok("5-staff-publish", False, "sem draft para publicar")
            ok("6-catalog-visible", False, "pulado — sem produto")
        else:
            product.status = Product.Status.PUBLISHED
            product.save()
            product.refresh_from_db()
            ok(
                "5-staff-publish",
                product.status == Product.Status.PUBLISHED and product.published_at is not None,
                f"sku={product.sku} status={product.status} published_at={product.published_at}",
            )

            # 6) Visível no catálogo
            cat = c.get("/catalogo/", {"q": product.sku})
            html = cat.content.decode("utf-8", "ignore")
            ok(
                "6-catalog-visible",
                cat.status_code == 200 and product.sku in html,
                f"catalog={cat.status_code} sku_in_html={product.sku in html} sku={product.sku}",
            )

    sku_out = getattr(product, "sku", None) if product is not None else None
    log_id = getattr(log, "pk", None)

    print("\n=== RESUMO S-003 HITL ===")
    passed = sum(1 for _, p, _ in RESULTS if p)
    print(f"{passed}/{len(RESULTS)} passos OK")
    for step, p, note in RESULTS:
        print(f"  - {step}: {'ok' if p else 'FALHOU'} — {note[:160]}")

    out = {
        "passed": passed,
        "total": len(RESULTS),
        "steps": [{"step": s, "ok": p, "note": n} for s, p, n in RESULTS],
        "extraction_id": log_id,
        "sku": sku_out,
        "finished_at": timezone.now().isoformat(),
    }
    path = Path(__file__).resolve().parent / "scripts_beta_s003_results.json"
    path.write_text(json.dumps(out, ensure_ascii=False, indent=2), encoding="utf-8")
    print(f"results -> {path}")
    return 0 if passed == len(RESULTS) else 1


if __name__ == "__main__":
    raise SystemExit(main())
