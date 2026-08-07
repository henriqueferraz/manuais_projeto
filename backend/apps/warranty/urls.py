from django.urls import path

from apps.warranty import views

app_name = "warranty"

urlpatterns = [
    path("<uuid:code_id>/", views.claim, name="claim"),
    path("<uuid:code_id>/qr.png", views.qr_png, name="qr_png"),
]
