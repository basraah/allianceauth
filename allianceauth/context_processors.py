from django.conf import settings
from .views import NightModeRedirectView


def auth_settings(request):
    return {
        'DOMAIN': settings.DOMAIN,
        'SITE_NAME': settings.SITE_NAME,
        'NIGHT_MODE': request.session.get(NightModeRedirectView.SESSION_VAR, False)
    }
