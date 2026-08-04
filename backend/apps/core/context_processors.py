"""Context processors do shell da loja."""


def brand(request):
    return {
        "brand_name": "TechParts AI",
        "brand_tagline": "Peças com precisão industrial",
    }
