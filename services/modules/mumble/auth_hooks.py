from __future__ import unicode_literals
from django.template.loader import render_to_string
from django.conf import settings
from notifications import notify

from alliance_auth import hooks
from authentication.models import AuthServicesInfo
from authentication.managers import AuthServicesInfoManager
from services.hooks import ServicesHook
from .manager import MumbleManager
from .tasks import disable_mumble, update_all_mumble_groups, update_mumble_groups
from .urls import urlpatterns

import logging

logger = logging.getLogger(__name__)


class MumbleService(ServicesHook):
    def __init__(self):
        ServicesHook.__init__(self)
        self.name = 'mumble'
        self.urlpatterns = urlpatterns
        self.service_url = settings.MUMBLE_URL

    def delete_user(self, user, notify_user=False):
        authinfo = AuthServicesInfo.objects.get_or_create(user=user)[0]
        if authinfo.mumble_username and authinfo.mumble_username != "":
            logger.debug("User %s has %s account %s. Deleting." % (user, self.name, authinfo.mumble_username))
            MumbleManager.delete_user(authinfo.mumble_username)
            AuthServicesInfoManager.update_user_mumble_info("", user)
            if notify_user:
                notify(user, 'Mumble Account Disabled', level='danger')
            return True

    def update_groups(self, user):
        logger.debug("Updating %s groups for %s" % (self.name, user))
        auth, c = AuthServicesInfo.objects.get_or_create(user=user)
        if auth.mumble_username:
            update_mumble_groups.delay(user.pk)

    def validate_user(self, user):
        auth = AuthServicesInfo.objects.get_or_create(user=user)[0]
        if auth.mumble_username and not self.service_active_for_user(user):
            self.delete_user(user, notify_user=True)

    def update_all_groups(self):
        logger.debug("Updating all %s groups" % self.name)
        update_all_mumble_groups.delay()

    def service_enabled_members(self):
        return settings.ENABLE_AUTH_MUMBLE or False

    def service_enabled_blues(self):
        return settings.ENABLE_BLUE_MUMBLE or False

    def render_services_ctrl(self, request):
        urls = self.Urls()
        urls.auth_activate = 'auth_activate_mumble'
        urls.auth_deactivate = 'auth_deactivate_mumble'
        urls.auth_reset_password = 'auth_reset_mumble_password'
        urls.auth_set_password = 'auth_set_mumble_password'
        username = AuthServicesInfo.objects.get_or_create(user=request.user)[0].mumble_username
        return render_to_string(self.service_ctrl_template, {
            'service_name': self.title,
            'urls': urls,
            'service_url': self.service_url,
            'username': username,
        }, request=request)


@hooks.register('services_hook')
def register_mumble_service():
    return MumbleService()
