from django.urls import path

from apps.channels import views

app_name = "channels"

urlpatterns = [
    path("whatsapp/webhook/", views.whatsapp_webhook, name="whatsapp_webhook"),
]
