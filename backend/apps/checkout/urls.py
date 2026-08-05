from django.urls import path

from apps.checkout import views

app_name = "checkout"

urlpatterns = [
    path("", views.checkout_start, name="start"),
    path("frete/", views.checkout_shipping, name="shipping"),
    path("pagamento/", views.checkout_payment, name="payment"),
    path("sucesso/<uuid:order_id>/", views.checkout_success, name="success"),
    path("api/frete/", views.quote_shipping, name="quote"),
    path("webhooks/pagamento/", views.payment_webhook, name="webhook"),
]
