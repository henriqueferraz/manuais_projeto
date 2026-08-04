"""Fila de revisão humana — alinhada ao protótipo AdminManualsView."""

from __future__ import annotations

import json

from django.contrib import messages
from django.contrib.auth.decorators import login_required, user_passes_test
from django.core.exceptions import ValidationError
from django.db.models import Count, Q
from django.http import HttpRequest, HttpResponse
from django.shortcuts import get_object_or_404, redirect, render
from django.utils import timezone
from django.views.decorators.http import require_http_methods

from apps.manuals.forms import ExtractionReviewForm, ManualUploadForm
from apps.manuals.models import ExtractionLog
from apps.manuals.services.pipeline import (
    approve_extraction,
    create_manual_from_upload,
    reject_extraction,
)
from apps.manuals.storage import signed_url


def _can_review(user) -> bool:
    if not user.is_authenticated:
        return False
    if user.is_superuser or user.is_staff:
        return True
    return user.groups.filter(name__in=("admin", "revisao_catalogo")).exists()


@login_required
@user_passes_test(_can_review)
def review_queue(request: HttpRequest) -> HttpResponse:
    qs = ExtractionLog.objects.select_related("manual", "draft_product", "reviewed_by")

    status_filter = request.GET.get("status", ExtractionLog.Status.AWAITING_REVIEW)
    q = request.GET.get("q", "").strip()

    if status_filter and status_filter != "all":
        qs = qs.filter(status=status_filter)
    if q:
        qs = qs.filter(
            Q(manual__original_filename__icontains=q)
            | Q(manual__manufacturer__icontains=q)
            | Q(raw_json__model_code__icontains=q)
            | Q(raw_json__sku_suggestion__icontains=q)
        )

    today = timezone.localdate()
    stats = ExtractionLog.objects.aggregate(
        awaiting=Count("id", filter=Q(status=ExtractionLog.Status.AWAITING_REVIEW)),
        failed=Count("id", filter=Q(status=ExtractionLog.Status.FAILED)),
        processed_today=Count(
            "id",
            filter=Q(finished_at__date=today)
            & ~Q(status=ExtractionLog.Status.PENDING)
            & ~Q(status=ExtractionLog.Status.RUNNING),
        ),
    )

    upload_form = ManualUploadForm()
    if request.method == "POST" and "upload" in request.POST:
        upload_form = ManualUploadForm(request.POST, request.FILES)
        if upload_form.is_valid():
            f = upload_form.cleaned_data["file"]
            try:
                content = f.read()
                create_manual_from_upload(
                    content=content,
                    filename=f.name,
                    user=request.user,
                    manufacturer=upload_form.cleaned_data.get("manufacturer") or "",
                )
                messages.success(request, "Manual enviado. Extração enfileirada.")
                return redirect("manuals:review_queue")
            except ValidationError as exc:
                messages.error(request, "; ".join(exc.messages))

    context = {
        "extractions": qs[:100],
        "stats": stats,
        "status_filter": status_filter,
        "q": q,
        "upload_form": upload_form,
        "status_choices": ExtractionLog.Status.choices,
    }
    return render(request, "manuals/review_queue.html", context)


@login_required
@user_passes_test(_can_review)
@require_http_methods(["GET", "POST"])
def review_detail(request: HttpRequest, pk: int) -> HttpResponse:
    log = get_object_or_404(
        ExtractionLog.objects.select_related("manual", "draft_product"),
        pk=pk,
    )
    form = ExtractionReviewForm(
        initial={
            "corrected_json": json.dumps(
                log.corrected_json or log.raw_json, ensure_ascii=False, indent=2
            ),
            "notes": log.review_notes,
        }
    )

    if request.method == "POST":
        form = ExtractionReviewForm(request.POST)
        action = request.POST.get("action")
        if form.is_valid():
            notes = form.cleaned_data.get("notes") or ""
            corrected = None
            raw = (form.cleaned_data.get("corrected_json") or "").strip()
            if raw:
                try:
                    corrected = json.loads(raw)
                except json.JSONDecodeError:
                    messages.error(request, "JSON corrigido inválido.")
                    return redirect("manuals:review_detail", pk=pk)

            try:
                if action == "approve":
                    product = approve_extraction(
                        log, reviewer=request.user, corrected=corrected, notes=notes
                    )
                    messages.success(
                        request,
                        f"Aprovado. Rascunho criado: {product.sku} (status=draft).",
                    )
                    return redirect("manuals:review_queue")
                if action == "reject":
                    reject_extraction(log, reviewer=request.user, notes=notes)
                    messages.warning(request, "Extração rejeitada.")
                    return redirect("manuals:review_queue")
            except Exception as exc:  # noqa: BLE001
                messages.error(request, str(exc))

    pdf_url = signed_url(log.manual.storage_key)
    return render(
        request,
        "manuals/review_detail.html",
        {
            "log": log,
            "form": form,
            "pdf_url": pdf_url,
            "raw_pretty": json.dumps(log.raw_json, ensure_ascii=False, indent=2),
        },
    )
