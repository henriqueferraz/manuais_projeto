from django.urls import path

from apps.partners import views

app_name = "partners"

urlpatterns = [
    path("", views.partner_list, name="list"),
]
