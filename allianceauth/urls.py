import esi.urls

from django.conf.urls import include, url
from django.contrib import admin
from django.views.generic.base import TemplateView

import allianceauth.authentication.views
import allianceauth.authentication.urls
import allianceauth.notifications.urls
import allianceauth.groupmanagement.urls
import allianceauth.services.urls
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

    # Services
    url(r'', include(allianceauth.services.urls)),
]

# Append app urls
app_urls = get_hooks('url_hook')
for app in app_urls:
    urlpatterns += [app().include_pattern]
