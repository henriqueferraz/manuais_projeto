from django.contrib import messages
from django.http import HttpRequest, HttpResponse
from django.shortcuts import get_object_or_404, redirect, render
from django.views.decorators.http import require_http_methods

from apps.subscriptions.models import Subscription, SubscriptionPlan


@require_http_methods(["GET", "POST"])
def plan_list(request: HttpRequest) -> HttpResponse:
    plans = SubscriptionPlan.objects.filter(active=True)
    if request.method == "POST":
        plan = get_object_or_404(SubscriptionPlan, pk=request.POST.get("plan_id"), active=True)
        email = (request.POST.get("email") or "").strip()
        if not email:
            messages.error(request, "Informe o e-mail.")
        else:
            sub = Subscription.start_mock(
                plan=plan,
                email=email,
                user=request.user if request.user.is_authenticated else None,
            )
            messages.success(
                request,
                f"Assinatura {sub.plan.name} ativada (mock) até {sub.current_period_end:%d/%m/%Y}.",
            )
            return redirect("subscriptions:plans")
    return render(request, "subscriptions/plans.html", {"plans": plans})
