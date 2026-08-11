"""Views do dashboard de insights e monitoramento (F7)."""

from __future__ import annotations

from django.contrib import messages
from django.contrib.auth.decorators import login_required, user_passes_test
from django.core.exceptions import ValidationError
from django.db.models import F, Q
from django.http import HttpRequest, HttpResponse, JsonResponse
from django.shortcuts import get_object_or_404, redirect, render
from django.urls import reverse
from django.utils import timezone
from django.views.decorators.http import require_GET, require_http_methods, require_POST

from apps.dashboard.forms import HomeHeroSlideForm
from apps.dashboard.models import HomeHeroSlide, OpsAlert
from apps.dashboard.services.metrics import collect_insights
from apps.dashboard.services.monitoring import collect_monitoring, simulate_incident
from apps.products.forms import InternalProductForm, initial_specs_from_product
from apps.products.image_validation import (
    PRODUCT_IMAGE_MAX_COUNT,
    gallery_image_count,
    prepare_product_image,
)
from apps.products.models import Product, ProductImage, ProductTranslation, Stock


def _is_ops(user) -> bool:
    if not user.is_authenticated:
        return False
    if user.is_superuser or user.is_staff:
        return True
    return user.groups.filter(name__in=("admin", "suporte", "revisao_catalogo")).exists()


@login_required
@user_passes_test(_is_ops)
@require_GET
def insights(request: HttpRequest) -> HttpResponse:
    try:
        days = int(request.GET.get("days") or 30)
    except (TypeError, ValueError):
        days = 30
    days = days if days in {7, 30, 90} else 30
    payload = collect_insights(days=days)
    return render(
        request,
        "dashboard/insights.html",
        {
            "insights": payload,
            "days": days,
            "page_title": "Dashboard de insights",
        },
    )


@login_required
@user_passes_test(_is_ops)
@require_GET
def monitoring(request: HttpRequest) -> HttpResponse:
    snap = collect_monitoring()
    return render(
        request,
        "dashboard/monitoring.html",
        {
            "snap": snap,
            "page_title": "Monitoramento",
        },
    )


@login_required
@user_passes_test(_is_ops)
@require_POST
def acknowledge_alert(request: HttpRequest, alert_id) -> HttpResponse:
    alert = get_object_or_404(OpsAlert, pk=alert_id)
    alert.acknowledged = True
    alert.acknowledged_by = request.user
    alert.acknowledged_at = timezone.now()
    alert.save(update_fields=["acknowledged", "acknowledged_by", "acknowledged_at", "updated_at"])
    messages.success(request, "Alerta reconhecido.")
    return redirect("dashboard:monitoring")


@login_required
@user_passes_test(_is_ops)
@require_http_methods(["POST"])
def simulate_incident_view(request: HttpRequest) -> HttpResponse:
    alert = simulate_incident()
    messages.warning(request, f"Incidente simulado criado: {alert.title}")
    if request.headers.get("Accept") == "application/json":
        return JsonResponse({"ok": True, "alert_id": str(alert.pk)})
    return redirect("dashboard:monitoring")


@login_required
@user_passes_test(_is_ops)
@require_GET
def home_hero_list(request: HttpRequest) -> HttpResponse:
    slides = HomeHeroSlide.objects.all()
    return render(
        request,
        "dashboard/home_hero.html",
        {
            "slides": slides,
            "page_title": "Hero da home",
            "form": HomeHeroSlideForm(),
        },
    )


@login_required
@user_passes_test(_is_ops)
@require_http_methods(["GET", "POST"])
def home_hero_edit(request: HttpRequest, pk: int | None = None) -> HttpResponse:
    slide = get_object_or_404(HomeHeroSlide, pk=pk) if pk else None
    if request.method == "POST":
        form = HomeHeroSlideForm(request.POST, request.FILES, instance=slide)
        if form.is_valid():
            saved = form.save()
            messages.success(
                request,
                "Slide atualizado." if slide else "Slide criado.",
            )
            return redirect("dashboard:home_hero_edit", pk=saved.pk)
    else:
        form = HomeHeroSlideForm(instance=slide)
    return render(
        request,
        "dashboard/home_hero_form.html",
        {
            "form": form,
            "slide": slide,
            "page_title": "Editar slide" if slide else "Novo slide",
        },
    )


@login_required
@user_passes_test(_is_ops)
@require_POST
def home_hero_toggle(request: HttpRequest, pk: int) -> HttpResponse:
    slide = get_object_or_404(HomeHeroSlide, pk=pk)
    slide.is_active = not slide.is_active
    slide.save(update_fields=["is_active", "updated_at"])
    messages.success(
        request,
        "Slide ativado." if slide.is_active else "Slide desativado.",
    )
    return redirect("dashboard:home_hero")


@login_required
@user_passes_test(_is_ops)
@require_POST
def home_hero_delete(request: HttpRequest, pk: int) -> HttpResponse:
    slide = get_object_or_404(HomeHeroSlide, pk=pk)
    title = slide.title
    if slide.image:
        slide.image.delete(save=False)
    slide.delete()
    messages.success(request, f"Slide removido: {title}")
    return redirect("dashboard:home_hero")


@login_required
@user_passes_test(_is_ops)
@require_GET
def products_list(request: HttpRequest) -> HttpResponse:
    status = request.GET.get("status", "").strip()
    kind = request.GET.get("kind", "").strip()
    q = request.GET.get("q", "").strip()
    low_stock = request.GET.get("low_stock") == "1"

    qs = Product.objects.select_related(
        "category", "stock", "equipment_model", "brand_ref"
    ).order_by("-updated_at")
    if status:
        qs = qs.filter(status=status)
    if kind:
        qs = qs.filter(product_kind=kind)
    if q:
        qs = qs.filter(
            Q(sku__icontains=q)
            | Q(brand__icontains=q)
            | Q(model_code__icontains=q)
            | Q(translations__name__icontains=q)
        ).distinct()
    if low_stock:
        qs = qs.filter(
            stock__isnull=False,
            stock__quantity_available__lte=F("stock__minimum_alert")
            + F("stock__quantity_reserved"),
        )

    return render(
        request,
        "dashboard/products.html",
        {
            "products": qs[:200],
            "status": status,
            "kind": kind,
            "q": q,
            "low_stock": low_stock,
            "status_choices": Product.Status.choices,
            "kind_choices": Product.Kind.choices,
            "page_title": "Estoque e produtos",
        },
    )


@login_required
@user_passes_test(_is_ops)
@require_http_methods(["GET", "POST"])
def products_edit(request: HttpRequest, pk: int | None = None) -> HttpResponse:
    product = get_object_or_404(Product, pk=pk) if pk else None
    stock = None
    product_images: list[ProductImage] = []
    gallery_count = 0
    initial = {}
    if product:
        product_images = list(product.images.order_by("sort_order", "id"))
        gallery_count = gallery_image_count(product)
        tr = product.translations.filter(locale="pt-BR").first()
        try:
            stock = product.stock
        except Stock.DoesNotExist:
            stock = None
        equipment_model_id = product.equipment_model_id
        if not equipment_model_id and product.model_code:
            from apps.catalog.models import EquipmentModel

            equipment_model_id = (
                EquipmentModel.objects.filter(code=product.model_code)
                .values_list("pk", flat=True)
                .first()
            )
        brand_ref_id = product.brand_ref_id
        if not brand_ref_id and product.brand:
            from apps.catalog.models import Brand

            brand_ref_id = (
                Brand.objects.filter(name__iexact=product.brand)
                .values_list("pk", flat=True)
                .first()
            )
        initial = {
            "sku": product.sku,
            "brand_ref": brand_ref_id,
            "equipment_model": equipment_model_id,
            "name": tr.name if tr else "",
            "description": tr.description if tr else "",
            "price": product.price,
            "voltage": product.voltage,
            "product_kind": product.product_kind,
            "status": product.status,
            "category": product.category_id,
            "quantity_available": stock.quantity_available if stock else 0,
            "minimum_alert": stock.minimum_alert if stock else 2,
        }
        initial.update(initial_specs_from_product(product))

    form = InternalProductForm(request.POST or None, initial=initial)
    image_errors: list[str] = []
    if request.method == "POST" and form.is_valid():
        data = form.cleaned_data
        delete_ids = {int(x) for x in request.POST.getlist("delete_images") if str(x).isdigit()}
        primary_raw = request.POST.get("primary_image") or ""
        primary_id = int(primary_raw) if primary_raw.isdigit() else None
        uploads = [f for f in request.FILES.getlist("images") if f]
        web_image_urls = [
            u.strip() for u in request.POST.getlist("web_image_urls") if str(u).strip()
        ]
        # Compat: seleção única antiga
        single = (request.POST.get("web_image_url") or "").strip()
        if single and single not in web_image_urls:
            web_image_urls.append(single)
        # Dedup preservando ordem
        seen_urls: set[str] = set()
        unique_web_urls: list[str] = []
        for url in web_image_urls:
            if url in seen_urls:
                continue
            seen_urls.add(url)
            unique_web_urls.append(url)
        web_image_urls = unique_web_urls[:PRODUCT_IMAGE_MAX_COUNT]

        kept_count = 0
        if product:
            kept_count = gallery_image_count(product, exclude_pks=delete_ids)
        remaining_slots = PRODUCT_IMAGE_MAX_COUNT - kept_count
        prepared_uploads = []
        web_images_attached = 0
        planned_count = len(uploads) + len(web_image_urls)
        if planned_count > remaining_slots:
            image_errors.append(
                f"Limite de {PRODUCT_IMAGE_MAX_COUNT} fotos. "
                f"Você pode adicionar no máximo {max(0, remaining_slots)} agora."
            )
        else:
            for upload in uploads:
                try:
                    prepared_uploads.append(prepare_product_image(upload))
                except ValidationError as exc:
                    msg = "; ".join(exc.messages) if hasattr(exc, "messages") else str(exc)
                    image_errors.append(f"{upload.name}: {msg}")
                    break
            if not image_errors and web_image_urls:
                from apps.dashboard.services.web_product_images import (
                    fetch_web_image_as_upload,
                )

                sku_stem = data.get("sku") or "produto"
                for idx, web_image_url in enumerate(web_image_urls, start=1):
                    try:
                        remote = fetch_web_image_as_upload(
                            web_image_url,
                            filename=f"{sku_stem}-web-{idx}.jpg",
                        )
                        prepared_uploads.append(prepare_product_image(remote))
                        web_images_attached += 1
                    except ValidationError as exc:
                        msg = "; ".join(exc.messages) if hasattr(exc, "messages") else str(exc)
                        image_errors.append(f"Foto da internet #{idx}: {msg}")
                        break

        if image_errors:
            from apps.dashboard.services.product_ai_assist import (
                related_part_modal_payload,
                related_spare_parts_for_product,
            )

            related = related_spare_parts_for_product(product) if product else []
            return render(
                request,
                "dashboard/products_form.html",
                {
                    "form": form,
                    "product": product,
                    "stock": stock,
                    "product_images": product_images,
                    "gallery_count": gallery_image_count(product) if product else 0,
                    "image_max_count": PRODUCT_IMAGE_MAX_COUNT,
                    "image_errors": image_errors,
                    "related_parts": related,
                    "related_parts_payload": [related_part_modal_payload(p) for p in related],
                    "page_title": f"Editar {product.sku}" if product else "Novo produto",
                    "ai_extract_url": reverse("dashboard:products_ai_extract"),
                    "web_image_search_url": reverse("dashboard:products_web_image_search"),
                },
            )

        if product is None:
            product = Product(sku=data["sku"])
        product.sku = data["sku"]
        brand_obj = data["brand_ref"]
        product.brand_ref = brand_obj
        product.brand = brand_obj.name if brand_obj else ""
        equipment_model = data["equipment_model"]
        product.equipment_model = equipment_model
        product.model_code = equipment_model.code if equipment_model else ""
        product.price = data["price"]
        product.voltage = data["voltage"]
        product.product_kind = data["product_kind"]
        product.status = data["status"]
        product.category = data["category"]
        product.power_w = data.get("power_w")
        product.weight_kg = data.get("weight_kg")
        product.dimensions = form.cleaned_dimensions()
        product.specs = form.cleaned_specs()
        product.save()
        ProductTranslation.objects.update_or_create(
            product=product,
            locale="pt-BR",
            defaults={"name": data["name"], "description": data["description"]},
        )
        stock, _ = Stock.objects.get_or_create(product=product)
        stock.quantity_available = data["quantity_available"]
        stock.minimum_alert = data["minimum_alert"]
        stock.save()

        extraction_raw = (request.POST.get("extraction_id") or "").strip()
        link_result = None
        if extraction_raw.isdigit():
            from apps.dashboard.services.product_ai_assist import (
                link_approved_extraction_to_product,
            )

            codes_raw = request.POST.get("selected_part_codes")
            if codes_raw is None:
                selected_codes = None
            else:
                selected_codes = {c.strip() for c in codes_raw.split(",") if c.strip()}

            link_result = link_approved_extraction_to_product(
                extraction_id=int(extraction_raw),
                product=product,
                user=request.user,
                selected_part_codes=selected_codes,
            )

        if delete_ids:
            for image in product.images.filter(pk__in=delete_ids):
                if image.image:
                    image.image.delete(save=False)
                image.delete()

        next_order = (
            product.images.order_by("-sort_order").values_list("sort_order", flat=True).first()
            or -1
        )
        created_ids: list[int] = []
        for upload in prepared_uploads:
            next_order += 1
            img = ProductImage(
                product=product,
                alt_text=data["name"][:255],
                sort_order=next_order,
                is_primary=False,
            )
            img.image.save(upload.name, upload, save=True)
            created_ids.append(img.pk)

        remaining = list(product.images.order_by("sort_order", "id"))
        if remaining:
            if primary_id and any(i.pk == primary_id for i in remaining):
                chosen = primary_id
            elif created_ids and not any(i.is_primary for i in remaining):
                chosen = created_ids[0]
            elif any(i.is_primary for i in remaining):
                chosen = next(i.pk for i in remaining if i.is_primary)
            else:
                chosen = remaining[0].pk
            product.images.update(is_primary=False)
            product.images.filter(pk=chosen).update(is_primary=True)

        messages.success(request, f"Produto {product.sku} salvo.")
        if web_images_attached:
            messages.info(
                request,
                (
                    f"{web_images_attached} foto(s) da internet anexada(s) ao produto."
                    if web_images_attached > 1
                    else "Foto da internet anexada ao produto (você escolheu uma das sugestões)."
                ),
            )
        if link_result:
            parts_n = int(link_result.get("parts_created") or 0) + int(
                link_result.get("parts_reused") or 0
            )
            bits = []
            if link_result.get("manual_linked"):
                bits.append("manual PDF vinculado (download na página do produto)")
            if parts_n:
                bits.append(f"{parts_n} peça(s) em rascunho")
            if bits:
                messages.info(
                    request,
                    "Extração vinculada: " + " · ".join(bits) + ". "
                    "Veja as peças na lista abaixo (mesmo formulário).",
                )
        return redirect("dashboard:products_edit", pk=product.pk)

    from apps.dashboard.services.product_ai_assist import (
        related_part_modal_payload,
        related_spare_parts_for_product,
    )

    related_parts = related_spare_parts_for_product(product) if product else []

    return render(
        request,
        "dashboard/products_form.html",
        {
            "form": form,
            "product": product,
            "stock": stock,
            "product_images": product_images,
            "gallery_count": gallery_count,
            "image_max_count": PRODUCT_IMAGE_MAX_COUNT,
            "image_errors": [],
            "related_parts": related_parts,
            "related_parts_payload": [related_part_modal_payload(p) for p in related_parts],
            "page_title": f"Editar {product.sku}" if product else "Novo produto",
            "ai_extract_url": reverse("dashboard:products_ai_extract"),
            "web_image_search_url": reverse("dashboard:products_web_image_search"),
        },
    )


@login_required
@user_passes_test(_is_ops)
@require_POST
def products_ai_extract(request: HttpRequest) -> JsonResponse:
    """Upload PDF (com antivírus) + extração IA — sem aplicar ao formulário."""
    from apps.dashboard.services.product_ai_assist import extract_manual_for_product_form

    upload = request.FILES.get("manual") or request.FILES.get("file")
    if upload is None:
        return JsonResponse({"ok": False, "error": "Selecione um arquivo PDF."}, status=400)

    try:
        content = upload.read()
        result = extract_manual_for_product_form(
            content=content,
            filename=upload.name or "manual.pdf",
            user=request.user,
            manufacturer=(request.POST.get("manufacturer") or "").strip(),
        )
    except ValidationError as exc:
        msg = "; ".join(exc.messages) if hasattr(exc, "messages") else str(exc)
        return JsonResponse({"ok": False, "error": msg}, status=400)
    except Exception as exc:  # noqa: BLE001
        return JsonResponse(
            {"ok": False, "error": f"Falha ao processar o PDF: {exc}"},
            status=500,
        )

    status = 200 if result.get("ok") else 422
    return JsonResponse(result, status=status)


@login_required
@user_passes_test(_is_ops)
@require_POST
def products_ai_discard(request: HttpRequest, extraction_id: int) -> JsonResponse:
    """Descarta a proposta da IA (não aplica nada)."""
    from apps.dashboard.services.product_ai_assist import discard_product_form_extraction
    from apps.manuals.models import ExtractionLog

    try:
        discard_product_form_extraction(
            extraction_id=extraction_id,
            user=request.user,
            notes=(request.POST.get("notes") or "Descartado no formulário de produto"),
        )
    except ExtractionLog.DoesNotExist:
        return JsonResponse({"ok": False, "error": "Extração não encontrada."}, status=404)
    except ValueError as exc:
        return JsonResponse({"ok": False, "error": str(exc)}, status=400)

    return JsonResponse({"ok": True, "extraction_id": extraction_id})


@login_required
@user_passes_test(_is_ops)
@require_POST
def products_web_image_search(request: HttpRequest) -> JsonResponse:
    """Busca até 5 fotos na internet a partir de marca, modelo e tipo de aparelho."""
    from apps.catalog.models import Brand, Category, EquipmentModel
    from apps.dashboard.services.web_product_images import search_product_web_images

    brand = (request.POST.get("brand") or "").strip()
    model = (request.POST.get("model") or "").strip()
    appliance_type = (request.POST.get("appliance_type") or "").strip()
    name = (request.POST.get("name") or "").strip()

    brand_ref = (request.POST.get("brand_ref") or "").strip()
    equipment_model = (request.POST.get("equipment_model") or "").strip()
    category = (request.POST.get("category") or "").strip()

    if brand_ref.isdigit() and not brand:
        brand = Brand.objects.filter(pk=int(brand_ref)).values_list("name", flat=True).first() or ""
    if equipment_model.isdigit() and not model:
        eq = EquipmentModel.objects.filter(pk=int(equipment_model)).first()
        if eq:
            model = (eq.code or eq.name or "").strip()
    if category.isdigit() and not appliance_type:
        appliance_type = (
            Category.objects.filter(pk=int(category)).values_list("name", flat=True).first() or ""
        )

    try:
        result = search_product_web_images(
            brand=brand,
            model=model,
            appliance_type=appliance_type,
            name=name,
        )
    except ValidationError as exc:
        msg = "; ".join(exc.messages) if hasattr(exc, "messages") else str(exc)
        return JsonResponse({"ok": False, "error": msg}, status=400)
    except Exception as exc:  # noqa: BLE001
        return JsonResponse(
            {"ok": False, "error": f"Falha ao buscar fotos: {exc}"},
            status=500,
        )

    return JsonResponse(result)


@login_required
@user_passes_test(_is_ops)
@require_POST
def products_delete(request: HttpRequest, pk: int) -> HttpResponse:
    product = get_object_or_404(Product, pk=pk)
    sku = product.sku
    for image in product.images.all():
        if image.image:
            image.image.delete(save=False)
    product.delete()
    messages.success(request, f"Produto {sku} excluído.")
    return redirect("dashboard:products")
