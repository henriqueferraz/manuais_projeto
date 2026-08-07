from django.urls import path

from apps.dashboard import views

app_name = "dashboard"

urlpatterns = [
    path("", views.insights, name="insights"),
    path("monitoramento/", views.monitoring, name="monitoring"),
    path("alertas/<uuid:alert_id>/ack/", views.acknowledge_alert, name="ack_alert"),
    path("incidentes/simular/", views.simulate_incident_view, name="simulate_incident"),
]
