from django.contrib import messages
from django.http import HttpRequest, HttpResponse
from django.shortcuts import get_object_or_404, redirect, render
from django.views.decorators.http import require_http_methods

from apps.subscriptions.billing import start_subscription
from apps.subscriptions.models import SubscriptionPlan


@require_http_methods(["GET", "POST"])
def plan_list(request: HttpRequest) -> HttpResponse:
    plans = SubscriptionPlan.objects.filter(active=True)
    if request.method == "POST":
        plan = get_object_or_404(SubscriptionPlan, pk=request.POST.get("plan_id"), active=True)
        email = (request.POST.get("email") or "").strip()
        payment_token = (request.POST.get("payment_token") or "").strip()
        if not email:
            messages.error(request, "Informe o e-mail.")
        else:
            result = start_subscription(
                plan=plan,
                email=email,
                user=request.user if request.user.is_authenticated else None,
                payment_token=payment_token,
            )
            if result.success and result.subscription:
                sub = result.subscription
                mode = sub.billing_provider or "mock"
                messages.success(
                    request,
                    f"Assinatura {sub.plan.name} ativada ({mode}) "
                    f"até {sub.current_period_end:%d/%m/%Y}.",
                )
                return redirect("subscriptions:plans")
            messages.error(request, result.failure_message or "Falha ao iniciar assinatura.")
    return render(request, "subscriptions/plans.html", {"plans": plans})
