from django.urls import path

from apps.dashboard import views

app_name = "dashboard"

urlpatterns = [
    path("", views.insights, name="insights"),
    path("monitoramento/", views.monitoring, name="monitoring"),
    path("alertas/<uuid:alert_id>/ack/", views.acknowledge_alert, name="ack_alert"),
    path("incidentes/simular/", views.simulate_incident_view, name="simulate_incident"),
    path("home-hero/", views.home_hero_list, name="home_hero"),
    path("home-hero/novo/", views.home_hero_edit, name="home_hero_create"),
    path("home-hero/<int:pk>/", views.home_hero_edit, name="home_hero_edit"),
    path("home-hero/<int:pk>/toggle/", views.home_hero_toggle, name="home_hero_toggle"),
    path("home-hero/<int:pk>/excluir/", views.home_hero_delete, name="home_hero_delete"),
]
