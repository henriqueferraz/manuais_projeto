from django.urls import path

from apps.compatibility import views

app_name = "compatibility"

urlpatterns = [
    path("verificar/", views.compatibility_checker, name="checker"),
    path("ops/produtos/", views.product_ops_list, name="ops_list"),
    path("ops/produtos/novo/", views.product_ops_edit, name="ops_create"),
    path("ops/produtos/<int:pk>/", views.product_ops_edit, name="ops_edit"),
    path("ops/compatibilidades/", views.compatibility_ops, name="ops_compat"),
]
