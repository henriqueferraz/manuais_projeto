"""Context processors do shell da loja."""

from django.conf import settings

from apps.cart.models import Cart
from apps.cart.services import CART_SESSION_KEY
from apps.core.branding import home_branding_urls


def brand(request):
    count = 0
    cart_id = request.session.get(CART_SESSION_KEY)
    if cart_id:
        cart = Cart.objects.filter(pk=cart_id).prefetch_related("items").first()
        if cart:
            count = sum(i.quantity for i in cart.items.all())
    ctx = {
        "brand_name": "TechParts AI",
        "brand_tagline": "Peças com precisão industrial",
        "cart_item_count": count,
        "pwa_enabled": bool(getattr(settings, "PWA_ENABLED", False)),
    }
    ctx.update(home_branding_urls())
    return ctx
