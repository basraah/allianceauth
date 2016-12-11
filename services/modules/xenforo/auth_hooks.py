from __future__ import unicode_literals

from django.conf import settings
from django.template.loader import render_to_string
from notifications import notify

from services.hooks import ServicesHook
from alliance_auth import hooks
from authentication.models import AuthServicesInfo
from authentication.managers import AuthServicesInfoManager

from .urls import urlpatterns
from .manager import XenForoManager

import logging

logger = logging.getLogger(__name__)


class XenforoService(ServicesHook):
    def __init__(self):
        ServicesHook.__init__(self)
        self.name = 'xenforo'
        self.urlpatterns = urlpatterns

    @property
    def title(self):
        return 'XenForo Forums'

    def delete_user(self, user, notify_user=False):
        authinfo = AuthServicesInfo.objects.get_or_create(user=user)[0]
        if authinfo.xenforo_username and authinfo.xenforo_password != "":
            logger.debug("User %s has a XenForo account %s. Deleting." % (user, authinfo.xenforo_username))
            XenForoManager.disable_user(authinfo.xenforo_username)
            AuthServicesInfoManager.update_user_xenforo_info("", user)
            if notify_user:
                notify(user, 'XenForo Account Disabled', level='danger')
            return True
        return False

    def validate_user(self, user):
        auth = AuthServicesInfo.objects.get_or_create(user=user)[0]
        if auth.xenforo_username and not self.service_active_for_user(user):
            self.delete_user(user, notify_user=True)

    def update_groups(self, user):
        pass

    def update_all_groups(self):
        pass

    def service_enabled_members(self):
        return settings.ENABLE_AUTH_XENFORO or False

    def service_enabled_blues(self):
        return settings.ENABLE_BLUE_XENFORO or False

    def render_services_ctrl(self, request):
        urls = self.Urls()
        urls.auth_activate = 'auth_activate_xenforo'
        urls.auth_deactivate = 'auth_deactivate_xenforo'
        urls.auth_reset_password = 'auth_reset_xenforo_password'
        urls.auth_set_password = 'auth_set_xenforo_password'
        username = AuthServicesInfo.objects.get_or_create(user=request.user)[0].xenforo_username
        return render_to_string(self.service_ctrl_template, {
            'service_name': self.title,
            'urls': urls,
            'service_url': '',
            'username': username
        }, request=request)


@hooks.register('services_hook')
def register_service():
    return XenforoService()
