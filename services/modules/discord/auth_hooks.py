from __future__ import unicode_literals

from django.template.loader import render_to_string
from django.conf import settings
from notifications import notify

from services.hooks import ServicesHook
from alliance_auth import hooks
from authentication.models import AuthServicesInfo
from authentication.managers import AuthServicesInfoManager

from .urls import urlpatterns
from .manager import DiscordOAuthManager
from .tasks import update_discord_groups, update_all_discord_groups

import logging

logger = logging.getLogger(__name__)


class DiscordService(ServicesHook):
    def __init__(self):
        ServicesHook.__init__(self)
        self.urlpatterns = urlpatterns
        self.name = 'discord'
        self.service_ctrl_template = 'registered/discord_service_ctrl.html'

    def delete_user(self, user, notify_user=False):
        authinfo = AuthServicesInfo.objects.get_or_create(user=user)[0]
        if authinfo.discord_uid and authinfo.discord_uid != "":
            logger.debug("User %s has discord account %s. Deleting." % (user, authinfo.discord_uid))
            DiscordOAuthManager.delete_user(authinfo.discord_uid)
            AuthServicesInfoManager.update_user_discord_info("", user)
            if notify_user:
                notify(user, 'Discord Account Disabled', level='danger')
            return True
        return False

    def update_groups(self, user):
        authinfo = AuthServicesInfo.objects.get_or_create(user=user)[0]
        if authinfo.discord_uid:
            update_discord_groups.delay(user.pk)

    def validate_user(self, user):
        auth = AuthServicesInfo.objects.get_or_create(user=user)[0]
        if auth.discord_uid and not self.service_active_for_user(user):
            self.delete_user(user, notify_user=True)

    def update_all_groups(self):
        update_all_discord_groups.delay()

    def service_enabled_members(self):
        return settings.ENABLE_AUTH_DISCORD or False

    def service_enabled_blues(self):
        return settings.ENABLE_BLUE_DISCORD or False

    def render_services_ctrl(self, request):
        authinfo = AuthServicesInfo.objects.get_or_create(user=request.user)[0]
        return render_to_string(self.service_ctrl_template, {
            'authinfo': authinfo,
        }, request=request)


@hooks.register('services_hook')
def register_service():
    return DiscordService()
