import esi.urls

import allianceauth.services.views
from django.conf.urls import include, url
from django.conf.urls.i18n import i18n_patterns
from django.contrib import admin
from django.utils.translation import ugettext_lazy as _
from django.views.generic.base import TemplateView

import allianceauth.authentication.views
import allianceauth.authentication.urls
import allianceauth.notifications.urls
import allianceauth.groupmanagement.urls
from allianceauth import NAME

from allianceauth.authentication import hmac_urls
from allianceauth.hooks import get_hooks

admin.site.site_header = NAME


# Functional/Untranslated URL's
urlpatterns = [
    # Locale
    url(r'^i18n/', include('django.conf.urls.i18n')),

    # Authentication
    url(r'', include(allianceauth.authentication.urls, namespace='authentication')),
    url(r'^account/login/$', TemplateView.as_view(template_name='public/login.html'), name='auth_login_user'),
    url(r'account/', include(hmac_urls)),

    # Admin urls
    url(r'^admin/', include(admin.site.urls)),

    # SSO
    url(r'^sso/', include(esi.urls, namespace='esi')),
    url(r'^sso/login$', allianceauth.authentication.views.sso_login, name='auth_sso_login'),

    # Notifications
    url(r'', include(allianceauth.notifications.urls)),

    # Groups
    url(r'', include(allianceauth.groupmanagement.urls)),
]

# User viewed/translated URLS
urlpatterns += i18n_patterns(
    # Group management


    url(_(r'^services/$'), allianceauth.services.views.services_view, name='auth_services'),

    # Tools
    url(_(r'^tool/fleet_formatter_tool/$'), allianceauth.services.views.fleet_formatter_view,
        name='auth_fleet_format_tool_view'),
)

# Append hooked service urls
services = get_hooks('services_hook')
for svc in services:
    urlpatterns += svc().urlpatterns

# Append app urls
app_urls = get_hooks('url_hook')
for app in app_urls:
    urlpatterns += [app().include_pattern]
