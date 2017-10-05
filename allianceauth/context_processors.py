from django.conf import settings
from .views import NightModeRedirectView


def auth_settings(request):
    return {
        'DOMAIN': settings.DOMAIN,
        'SITE_NAME': settings.SITE_NAME,
        'NIGHT_MODE': NightModeRedirectView.night_mode_state(request),
    }
