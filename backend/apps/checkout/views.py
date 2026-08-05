"""Views do checkout multi-step + webhook de pagamento."""

from __future__ import annotations

import json

from django.contrib import messages
from django.core.exceptions import ValidationError
from django.http import HttpRequest, HttpResponse, JsonResponse
from django.shortcuts import get_object_or_404, redirect, render
from django.views.decorators.csrf import csrf_exempt
from django.views.decorators.http import require_http_methods, require_POST

from apps.cart.coupons import COUPON_SESSION_KEY, cart_totals_with_coupon
from apps.cart.services import cart_totals, get_or_create_cart
from apps.checkout.forms import CheckoutAddressForm, CheckoutPaymentForm, CheckoutShippingForm
from apps.checkout.payments import parse_webhook_event, verify_webhook_signature
from apps.checkout.services import apply_payment_webhook, build_order_from_cart, pay_order
from apps.checkout.shipping import calculate_shipping
from apps.orders.models import Order

SESSION_CHECKOUT = "checkout_draft"


def _cart_checkout_totals(request: HttpRequest):
    from decimal import Decimal

    cart = get_or_create_cart(request)
    code = (request.session.get(COUPON_SESSION_KEY) or "").strip()
    if code:
        try:
            return cart, cart_totals_with_coupon(cart, code), code
        except ValidationError:
            request.session.pop(COUPON_SESSION_KEY, None)
    base = cart_totals(cart)
    base["discount"] = Decimal("0")
    base["coupon"] = None
    base["total_after_discount"] = base["subtotal"]
    return cart, base, ""


def _draft(request: HttpRequest) -> dict:
    return request.session.get(SESSION_CHECKOUT, {})


def _save_draft(request: HttpRequest, data: dict) -> None:
    draft = _draft(request)
    draft.update(data)
    request.session[SESSION_CHECKOUT] = draft
    request.session.modified = True


@require_http_methods(["GET", "POST"])
def checkout_start(request: HttpRequest) -> HttpResponse:
    cart, totals, _coupon = _cart_checkout_totals(request)
    if not totals["items"]:
        messages.warning(request, "Seu carrinho está vazio.")
        return redirect("cart:detail")

    form = CheckoutAddressForm(request.POST or None, initial=_draft(request))
    if request.method == "POST" and form.is_valid():
        _save_draft(request, form.cleaned_data)
        return redirect("checkout:shipping")

    return render(
        request,
        "checkout/step_address.html",
        {"form": form, "totals": totals, "step": 1},
    )


@require_http_methods(["GET", "POST"])
def checkout_shipping(request: HttpRequest) -> HttpResponse:
    draft = _draft(request)
    if not draft.get("shipping_cep"):
        return redirect("checkout:start")

    cart, totals, _coupon = _cart_checkout_totals(request)
    try:
        options = calculate_shipping(
            cep=draft["shipping_cep"],
            subtotal=totals["total_after_discount"],
        )
    except ValueError as exc:
        messages.error(request, str(exc))
        return redirect("checkout:start")

    form = CheckoutShippingForm(request.POST or None)
    if request.method == "POST" and form.is_valid():
        opt_id = form.cleaned_data["shipping_option_id"]
        if not any(o.id == opt_id for o in options):
            messages.error(request, "Selecione uma opção de frete válida.")
        else:
            _save_draft(request, {"shipping_option_id": opt_id})
            return redirect("checkout:payment")

    return render(
        request,
        "checkout/step_shipping.html",
        {
            "form": form,
            "options": options,
            "totals": totals,
            "draft": draft,
            "step": 2,
        },
    )


@require_http_methods(["GET", "POST"])
def checkout_payment(request: HttpRequest) -> HttpResponse:
    draft = _draft(request)
    if not draft.get("shipping_option_id"):
        return redirect("checkout:shipping")

    cart, totals, coupon_code = _cart_checkout_totals(request)
    form = CheckoutPaymentForm(request.POST or None)

    if request.method == "POST" and form.is_valid():
        try:
            order = build_order_from_cart(
                cart=cart,
                email=draft["email"],
                shipping=draft,
                shipping_option_id=draft["shipping_option_id"],
                user=request.user,
                coupon_code=coupon_code,
            )
            pay_order(order=order, payment_token=form.cleaned_data["payment_token"])
            request.session.pop(SESSION_CHECKOUT, None)
            request.session.pop(COUPON_SESSION_KEY, None)
            messages.success(request, f"Pedido {order.number} pago com sucesso.")
            return redirect("checkout:success", order_id=order.id)
        except ValidationError as exc:
            messages.error(request, "; ".join(getattr(exc, "messages", [str(exc)])))
        except Exception as exc:  # noqa: BLE001
            messages.error(request, f"Erro no checkout: {exc}")

    return render(
        request,
        "checkout/step_payment.html",
        {"form": form, "totals": totals, "draft": draft, "step": 3},
    )


def checkout_success(request: HttpRequest, order_id) -> HttpResponse:
    order = get_object_or_404(Order.objects.prefetch_related("items", "payments"), pk=order_id)
    return render(request, "checkout/success.html", {"order": order, "step": 4})


@csrf_exempt
@require_POST
def payment_webhook(request: HttpRequest) -> HttpResponse:
    signature = request.headers.get("X-Signature") or request.headers.get("Stripe-Signature", "")
    payload = request.body
    if not verify_webhook_signature(payload=payload, signature_header=signature):
        return JsonResponse({"error": "invalid signature"}, status=400)

    try:
        event = parse_webhook_event(payload)
    except json.JSONDecodeError:
        return JsonResponse({"error": "invalid json"}, status=400)

    provider_payment_id = (
        event.get("provider_payment_id")
        or event.get("data", {}).get("object", {}).get("id")
        or event.get("data", {}).get("id")
        or ""
    )
    status = event.get("status") or event.get("type") or event.get("action") or ""
    # normaliza tipos stripe
    if status in {"payment_intent.succeeded", "charge.succeeded"}:
        status = "paid"
    elif status in {"payment_intent.payment_failed", "charge.failed"}:
        status = "failed"
    elif status in {"charge.refunded"}:
        status = "refunded"

    payment = apply_payment_webhook(
        provider_payment_id=str(provider_payment_id),
        event_status=str(status),
        raw=event,
    )
    return JsonResponse({"ok": True, "found": payment is not None})


@require_http_methods(["GET"])
def quote_shipping(request: HttpRequest) -> JsonResponse:
    cep = request.GET.get("cep", "")
    cart = get_or_create_cart(request)
    totals = cart_totals(cart)
    try:
        options = calculate_shipping(cep=cep, subtotal=totals["subtotal"])
    except ValueError as exc:
        return JsonResponse({"error": str(exc)}, status=400)
    return JsonResponse({"options": [o.as_dict() for o in options]})
