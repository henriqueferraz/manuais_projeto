from django.urls import path

from apps.cart import views

app_name = "cart"

urlpatterns = [
    path("", views.cart_detail, name="detail"),
    path("adicionar/", views.cart_add, name="add"),
    path("atualizar/", views.cart_update, name="update"),
    path("remover/", views.cart_remove, name="remove"),
]
