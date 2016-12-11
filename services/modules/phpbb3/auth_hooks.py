from __future__ import unicode_literals

from django.conf import settings
from django.template.loader import render_to_string
from notifications import notify

from services.hooks import ServicesHook
from alliance_auth import hooks
from authentication.models import AuthServicesInfo
from authentication.managers import AuthServicesInfoManager

from .urls import urlpatterns
from .manager import Phpbb3Manager
from .tasks import update_all_forum_groups, update_forum_groups

import logging

logger = logging.getLogger(__name__)


class Phpbb3Service(ServicesHook):
    def __init__(self):
        ServicesHook.__init__(self)
        self.name = 'phpbb3'
        self.urlpatterns = urlpatterns
        self.service_url = settings.FORUM_URL  # TODO: This needs to be renamed at some point...

    @property
    def title(self):
        return 'phpBB3 Forum'

    def delete_user(self, user, notify_user=False):
        authinfo = AuthServicesInfo.objects.get_or_create(user=user)[0]
        if authinfo.forum_username and authinfo.forum_username != "":
            logger.debug("User %s has forum account %s. Deleting." % (user, authinfo.forum_username))
            Phpbb3Manager.disable_user(authinfo.forum_username)
            AuthServicesInfoManager.update_user_forum_info("", user)
            if notify_user:
                notify(user, 'Forum Account Disabled', level='danger')
            return True
        return False

    def validate_user(self, user):
        auth = AuthServicesInfo.objects.get_or_create(user=user)[0]
        if auth.forum_username and not self.service_active_for_user(user):
            self.delete_user(user, notify_user=True)

    def update_groups(self, user):
        auth, c = AuthServicesInfo.objects.get_or_create(user=user)
        if auth.forum_username:
            update_forum_groups.delay(user.pk)

    def update_all_groups(self):
        update_all_forum_groups.delay()

    def service_enabled_members(self):
        return settings.ENABLE_AUTH_FORUM or False  # TODO: Rename this setting

    def service_enabled_blues(self):
        return settings.ENABLE_BLUE_FORUM or False  # TODO: Rename this setting

    def render_services_ctrl(self, request):
        urls = self.Urls()
        urls.auth_activate = 'auth_activate_phpbb3'
        urls.auth_deactivate = 'auth_deactivate_phpbb3'
        urls.auth_reset_password = 'auth_reset_phpbb3_password'
        urls.auth_set_password = 'auth_set_phpbb3_password'
        username = AuthServicesInfo.objects.get_or_create(user=request.user)[0].forum_username
        return render_to_string(self.service_ctrl_template, {
            'service_name': self.title,
            'urls': urls,
            'service_url': self.service_url,
            'username': username
        }, request=request)


@hooks.register('services_hook')
def register_service():
    return Phpbb3Service()
