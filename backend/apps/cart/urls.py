from django.urls import path

from apps.cart import views

app_name = "cart"

urlpatterns = [
    path("", views.cart_detail, name="detail"),
    path("adicionar/", views.cart_add, name="add"),
    path("atualizar/", views.cart_update, name="update"),
    path("remover/", views.cart_remove, name="remove"),
    path("cupom/", views.cart_apply_coupon, name="apply_coupon"),
    path("cupom/remover/", views.cart_remove_coupon, name="remove_coupon"),
]
