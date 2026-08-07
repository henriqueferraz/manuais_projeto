from django.urls import path

from apps.subscriptions import views

app_name = "subscriptions"

urlpatterns = [
    path("", views.plan_list, name="plans"),
]
