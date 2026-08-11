from django.urls import path

from apps.catalog import views

app_name = "catalog"

urlpatterns = [
    path("", views.product_list, name="list"),
    path("autocomplete/", views.search_autocomplete, name="autocomplete"),
    path("<slug:slug>/manual/", views.product_manual_download, name="manual_download"),
    path("<slug:slug>/", views.product_detail, name="detail"),
]
