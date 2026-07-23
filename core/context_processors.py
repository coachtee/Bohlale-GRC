from django.conf import settings


def build_info(request):
    """Small, harmless context available on every template."""
    return {
        "BOHLALE_APP_NAME": "Bohlale GRC",
        "BOHLALE_DEBUG": settings.DEBUG,
    }
