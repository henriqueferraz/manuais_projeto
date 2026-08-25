from django.urls import path

from . import views

app_name = "core"

urlpatterns = [
    path("", views.HomeView.as_view(), name="home"),
    path("health/", views.health, name="health"),
    path("ops/hooks/lowcode/", views.lowcode_hook, name="lowcode_hook"),
    path("ops/hooks/lowcode/report/", views.lowcode_report, name="lowcode_report"),
    path("sw.js", views.service_worker, name="service_worker"),
]
