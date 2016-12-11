from __future__ import unicode_literals

from django.conf import settings
from django.template.loader import render_to_string
from notifications import notify

from services.hooks import ServicesHook, MenuItemHook
from alliance_auth import hooks
from authentication.models import AuthServicesInfo
from authentication.managers import AuthServicesInfoManager

from .urls import urlpatterns
from .manager import OpenfireManager
from .tasks import update_all_jabber_groups, update_jabber_groups

import logging

logger = logging.getLogger(__name__)


class OpenfireService(ServicesHook):
    def __init__(self):
        ServicesHook.__init__(self)
        self.name = 'openfire'
        self.urlpatterns = urlpatterns
        self.service_url = settings.JABBER_URL

    @property
    def title(self):
        return "Jabber"

    def delete_user(self, user, notify_user=False):
        authinfo = AuthServicesInfo.objects.get_or_create(user=user)[0]
        if authinfo.jabber_username and authinfo.jabber_username != "":
            logger.debug("User %s has jabber account %s. Deleting." % (user, authinfo.jabber_username))
            OpenfireManager.delete_user(authinfo.jabber_username)
            AuthServicesInfoManager.update_user_jabber_info("", user)
            if notify_user:
                notify(user, 'Jabber Account Disabled', level='danger')
            return True
        return False

    def validate_user(self, user):
        auth = AuthServicesInfo.objects.get_or_create(user=user)[0]
        if auth.jabber_username and not self.service_active_for_user(user):
            self.delete_user(user, notify_user=True)

    def update_groups(self, user):
        auth, c = AuthServicesInfo.objects.get_or_create(user=user)
        if auth.jabber_username:
            update_jabber_groups.delay(user.pk)

    def update_all_groups(self):
        update_all_jabber_groups.delay()

    def service_enabled_members(self):
        return settings.ENABLE_AUTH_JABBER or False  # TODO: Rename this setting

    def service_enabled_blues(self):
        return settings.ENABLE_BLUE_JABBER or False  # TODO: Rename this setting

    def render_services_ctrl(self, request):
        """
        Example for rendering the service control panel row
        You can override the default template and create a
        custom one if you wish.
        :param request:
        :return:
        """
        urls = self.Urls()
        urls.auth_activate = 'auth_activate_openfire'
        urls.auth_deactivate = 'auth_deactivate_openfire'
        urls.auth_reset_password = 'auth_reset_openfire_password'
        username = AuthServicesInfo.objects.get_or_create(user=request.user)[0].jabber_username
        return render_to_string(self.service_ctrl_template, {
            'service_name': self.title,
            'urls': urls,
            'service_url': self.service_url,
            'username': username
        }, request=request)


@hooks.register('services_hook')
def register_service():
    return OpenfireService()


class JabberBroadcast(MenuItemHook):
    def __init__(self):
        MenuItemHook.__init__(self,
                              'Jabber Broadcast',
                              'fa fa-lock fa-fw fa-bullhorn grayiconecolor',
                              'auth_jabber_broadcast_view')

    def render(self, request):
        if request.user.has_perm('auth.jabber_broadcast'):
            return MenuItemHook.render(self, request)
        return ''


@hooks.register('menu_util_hook')
def register_menu():
    return JabberBroadcast()
