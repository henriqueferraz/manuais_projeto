from django.urls import path

from apps.orders import views_returns

app_name = "returns"

urlpatterns = [
    path("", views_returns.return_list, name="list"),
    path("operacao/", views_returns.returns_ops_panel, name="ops"),
    path("<uuid:pk>/", views_returns.return_detail, name="detail"),
    path("<uuid:pk>/processar/", views_returns.returns_process, name="process"),
]
