from __future__ import unicode_literals

from django.conf import settings
from django.template.loader import render_to_string
from notifications import notify

from services.hooks import ServicesHook
from alliance_auth import hooks

from .urls import urlpatterns
from .tasks import update_teamspeak3_groups, update_all_teamspeak3_groups
from .manager import Teamspeak3Manager

from authentication.managers import AuthServicesInfoManager
from authentication.models import AuthServicesInfo

import logging

logger = logging.getLogger(__name__)


class Teamspeak3Service(ServicesHook):
    def __init__(self):
        ServicesHook.__init__(self)
        self.name = 'teamspeak3'
        self.urlpatterns = urlpatterns
        self.service_ctrl_template = 'registered/teamspeak3_service_ctrl.html'

    def delete_user(self, user, notify_user=False):
        authinfo = AuthServicesInfo.objects.get_or_create(user=user)[0]
        if authinfo.teamspeak3_uid and authinfo.teamspeak3_uid != "":
            logger.debug("User %s has %s account %s. Deleting." % (user, self.name, authinfo.teamspeak3_uid))
            Teamspeak3Manager.delete_user(authinfo.teamspeak3_uid)
            AuthServicesInfoManager.update_user_teamspeak3_info("", "", user)
            if notify_user:
                notify(user, 'TeamSpeak3 Account Disabled', level='danger')
            return True
        return False

    def update_groups(self, user):
        logger.debug("Updating %s groups for %s" % (self.name, user))
        update_teamspeak3_groups.delay(user.pk)

    def validate_user(self, user):
        auth = AuthServicesInfo.objects.get_or_create(user=user)[0]
        if auth.teamspeak3_uid and not self.service_active_for_user(user):
            self.delete_user(user, notify_user=True)

    def update_all_groups(self):
        logger.debug("Updating all %s groups" % self.name)
        update_all_teamspeak3_groups.delay()

    def service_enabled_members(self):
        return settings.ENABLE_AUTH_TEAMSPEAK3 or False

    def service_enabled_blues(self):
        return settings.ENABLE_BLUE_TEAMSPEAK3 or False

    def render_services_ctrl(self, request):
        authinfo = AuthServicesInfo.objects.get_or_create(user=request.user)[0]
        return render_to_string(self.service_ctrl_template, {
            'authinfo': authinfo,
        }, request=request)


@hooks.register('services_hook')
def register_service():
    return Teamspeak3Service()
