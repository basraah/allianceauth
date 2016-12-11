from __future__ import unicode_literals

from django.conf import settings
from django.template.loader import render_to_string
from notifications import notify

from services.hooks import ServicesHook
from alliance_auth import hooks
from authentication.models import AuthServicesInfo
from authentication.managers import AuthServicesInfoManager

from .urls import urlpatterns
from .manager import smfManager
from .tasks import update_all_smf_groups, update_smf_groups

import logging

logger = logging.getLogger(__name__)


class SmfService(ServicesHook):
    def __init__(self):
        ServicesHook.__init__(self)
        self.name = 'smf'
        self.urlpatterns = urlpatterns
        self.service_url = settings.SMF_URL

    @property
    def title(self):
        return 'SMF Forums'

    def delete_user(self, user, notify_user=False):
        authinfo = AuthServicesInfo.objects.get_or_create(user=user)[0]
        if authinfo.smf_username and authinfo.smf_username != "":
            logger.debug("User %s has a SMF account %s. Deleting." % (user, authinfo.smf_username))
            smfManager.disable_user(authinfo.smf_username)
            AuthServicesInfoManager.update_user_smf_info("", user)
            if notify_user:
                notify(user, "SMF Account Disabled", level='danger')
            return True
        return False

    def validate_user(self, user):
        auth = AuthServicesInfo.objects.get_or_create(user=user)[0]
        if auth.smf_username and not self.service_active_for_user(user):
            self.delete_user(user)

    def update_groups(self, user):
        auth, c = AuthServicesInfo.objects.get_or_create(user=user)
        if auth.smf_username:
            update_smf_groups.delay(user.pk)

    def update_all_groups(self):
        update_all_smf_groups.delay()

    def service_enabled_members(self):
        return settings.ENABLE_AUTH_SMF or False

    def service_enabled_blues(self):
        return settings.ENABLE_BLUE_SMF or False

    def render_services_ctrl(self, request):
        urls = self.Urls()
        urls.auth_activate = 'auth_activate_smf'
        urls.auth_deactivate = 'auth_deactivate_smf'
        urls.auth_reset_password = 'auth_reset_smf_password'
        urls.auth_set_password = 'auth_set_smf_password'
        username = AuthServicesInfo.objects.get_or_create(user=request.user)[0].smf_username
        return render_to_string(self.service_ctrl_template, {
            'service_name': self.title,
            'urls': urls,
            'service_url': self.service_url,
            'username': username
        }, request=request)


@hooks.register('services_hook')
def register_service():
    return SmfService()
