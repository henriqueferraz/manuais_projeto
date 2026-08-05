from django.contrib import admin
from django.contrib.auth import views as auth_views
from django.urls import include, path
from two_factor.urls import urlpatterns as two_factor_patterns

urlpatterns = [
    path("admin/", admin.site.urls),
    path("", include(two_factor_patterns)),
    path(
        "account/logout/",
        auth_views.LogoutView.as_view(),
        name="logout",
    ),
    path("", include("apps.core.urls")),
    path("manuais/", include("apps.manuals.urls")),
    path("catalogo/", include("apps.catalog.urls")),
    path("carrinho/", include("apps.cart.urls")),
    path("checkout/", include("apps.checkout.urls")),
    path("compatibilidade/", include("apps.compatibility.urls")),
]
