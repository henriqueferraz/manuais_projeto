from django.urls import path

from apps.tickets import views

app_name = "tickets"

urlpatterns = [
    path("", views.ticket_list, name="list"),
    path("suporte/", views.support_panel, name="support"),
    path("<str:code>/", views.ticket_detail, name="detail"),
    path("<str:code>/status/", views.support_update_status, name="update_status"),
]
