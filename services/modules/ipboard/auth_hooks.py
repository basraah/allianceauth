from __future__ import unicode_literals

from django.conf import settings
from django.template.loader import render_to_string
from notifications import notify

from services.hooks import ServicesHook
from alliance_auth import hooks
from authentication.models import AuthServicesInfo
from authentication.managers import AuthServicesInfoManager

from .urls import urlpatterns
from .tasks import update_all_ipboard_groups, update_ipboard_groups
from .manager import IPBoardManager

import logging

logger = logging.getLogger(__name__)


class IpboardService(ServicesHook):
    def __init__(self):
        ServicesHook.__init__(self)
        self.name = 'ipboard'
        self.service_url = settings.IPBOARD_ENDPOINT or None
        self.urlpatterns = urlpatterns

    @property
    def title(self):
        return 'IPBoard Forums'

    def delete_user(self, user, notify_user=False):
        auth = AuthServicesInfo.objects.get_or_create(user=user)[0]
        result = IPBoardManager.disable_user(auth.ipboard_username)
        AuthServicesInfoManager.update_user_ipboard_info("", user)
        if notify_user:
            notify(user, 'IPBoard Account Disabled', level='danger')
        return result

    def update_groups(self, user):
        logger.debug("Updating %s groups for %s" % (self.name, user))
        auth, c = AuthServicesInfo.objects.get_or_create(user=user)
        if auth.ipboard_username:
            update_ipboard_groups.delay(user.pk)

    def validate_user(self, user):
        auth = AuthServicesInfo.objects.get_or_create(user=user)[0]
        if auth.ipboard_username and not self.service_active_for_user(user):
            self.delete_user(user, notify_user=True)

    def update_all_groups(self):
        update_all_ipboard_groups.delay()

    def service_enabled_members(self):
        return settings.ENABLE_AUTH_IPBOARD or False

    def service_enabled_blues(self):
        return settings.ENABLE_BLUE_IPBOARD or False

    def render_services_ctrl(self, request):
        urls = self.Urls()
        urls.auth_activate = 'auth_activate_ipboard'
        urls.auth_deactivate = 'auth_deactivate_ipboard'
        urls.auth_reset_password = 'auth_reset_ipboard_password'
        urls.auth_set_password = 'auth_set_ipboard_password'
        username = AuthServicesInfo.objects.get_or_create(user=request.user)[0].ipboard_username
        return render_to_string(self.service_ctrl_template, {
            'service_name': self.title,
            'urls': urls,
            'service_url': self.service_url,
            'username': username
        }, request=request)


@hooks.register('services_hook')
def register_service():
    return IpboardService()
