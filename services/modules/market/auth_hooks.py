from __future__ import unicode_literals

from django.conf import settings
from django.template.loader import render_to_string

from services.hooks import ServicesHook
from alliance_auth import hooks
from authentication.models import AuthServicesInfo
from authentication.managers import AuthServicesInfoManager

from .urls import urlpatterns
from .manager import marketManager

import logging

logger = logging.getLogger(__name__)


class MarketService(ServicesHook):
    def __init__(self):
        ServicesHook.__init__(self)
        self.name = 'market'
        self.urlpatterns = urlpatterns
        self.service_url = settings.MARKET_URL

    @property
    def title(self):
        return "Alliance Market"

    def delete_user(self, user, notify_user=False):
        authinfo = AuthServicesInfo.objects.get_or_create(user=user)[0]
        if authinfo.market_username and authinfo.market_username != "":
            logger.debug("User %s has a Market account %s. Deleting." % (user, authinfo.market_username))
            marketManager.disable_user(authinfo.market_username)
            AuthServicesInfoManager.update_user_market_info("", user)
            if notify_user:
                notify(user, 'Alliance Market Account Disabled', level='danger')
            return True
        return False

    def update_groups(self, user):
        pass

    def validate_user(self, user):
        auth = AuthServicesInfo.objects.get_or_create(user=user)[0]
        if auth.market_username and self.service_active_for_user(user):
            self.delete_user(user)

    def update_all_groups(self):
        pass

    def service_enabled_members(self):
        return settings.ENABLE_AUTH_MARKET or False

    def service_enabled_blues(self):
        return settings.ENABLE_BLUE_MARKET or False

    def render_services_ctrl(self, request):
        urls = self.Urls()
        urls.auth_activate = 'auth_activate_market'
        urls.auth_deactivate = 'auth_deactivate_market'
        urls.auth_reset_password = 'auth_reset_market_password'
        urls.auth_set_password = 'auth_set_market_password'
        username = AuthServicesInfo.objects.get_or_create(user=request.user)[0].market_username
        return render_to_string(self.service_ctrl_template, {
            'service_name': self.title,
            'urls': urls,
            'service_url': self.service_url,
            'username': username
        }, request=request)


@hooks.register('services_hook')
def register_service():
    return MarketService()
