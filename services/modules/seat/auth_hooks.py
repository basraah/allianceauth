from __future__ import unicode_literals

from django.template.loader import render_to_string
from django.conf import settings

from services.hooks import ServicesHook
from alliance_auth import hooks

from .urls import urlpatterns
from .tasks import SeatTasks

import logging

logger = logging.getLogger(__name__)


class SeatService(ServicesHook):
    def __init__(self):
        ServicesHook.__init__(self)
        self.urlpatterns = urlpatterns
        self.name = 'seat'
        self.service_url = settings.SEAT_URL

    @property
    def title(self):
        return "SeAT"

    def delete_user(self, user, notify_user=False):
        logger.debug('Deleting user %s %s account' % (user, self.name))
        return SeatTasks.delete_user(user, notify_user=notify_user)

    def validate_user(self, user):
        logger.debug('Validating user %s %s account' % (user, self.name))
        if SeatTasks.has_account(user) and self.service_active_for_user(user):
            self.delete_user(user)

    def update_groups(self, user):
        logger.debug("Updating %s groups for %s" % (self.name, user))
        if SeatTasks.has_account(user):
            SeatTasks.update_roles.delay(user.pk)

    def update_all_groups(self):
        logger.debug('Update all %s groups called' % self.name)
        SeatTasks.update_all_roles.delay()

    def service_enabled_members(self):
        return settings.ENABLE_AUTH_SEAT or False

    def service_enabled_blues(self):
        return settings.ENABLE_BLUE_SEAT or False

    def render_services_ctrl(self, request):
        urls = self.Urls()
        urls.auth_activate = 'auth_activate_seat'
        urls.auth_deactivate = 'auth_deactivate_seat'
        urls.auth_reset_password = 'auth_reset_seat_password'
        urls.auth_set_password = 'auth_set_seat_password'
        return render_to_string(self.service_ctrl_template, {
            'service_name': self.title,
            'urls': urls,
            'service_url': self.service_url,
            'username': request.user.seat.username if SeatTasks.has_account(request.user) else ''
        }, request=request)


@hooks.register('services_hook')
def register_service():
    return SeatService()
