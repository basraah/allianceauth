from __future__ import unicode_literals

from django.conf import settings
from django.template.loader import render_to_string
from django.contrib import messages
from notifications import notify

from services.hooks import ServicesHook
from alliance_auth import hooks
from authentication.models import AuthServicesInfo
from eveonline.models import EveCharacter

from .urls import urlpatterns
from .manager import DiscourseManager
from .tasks import update_discourse_groups, update_all_discourse_groups

import logging

logger = logging.getLogger(__name__)


class DiscourseService(ServicesHook):
    def __init__(self):
        ServicesHook.__init__(self)
        self.urlpatterns = urlpatterns
        self.name = 'discourse'
        self.service_ctrl_template = 'registered/discourse_service_ctrl.html'

    def delete_user(self, user, notify_user=False):
        authinfo = AuthServicesInfo.objects.get_or_create(user=user)[0]
        if authinfo.discourse_enabled:
            logger.debug("User %s has a Discourse account. Disabling login." % user)
            DiscourseManager.disable_user(user)
            authinfo.discourse_enabled = False
            authinfo.save()
            if notify_user:
                notify(user, 'Discourse Account Disabled', level='danger')
            return True
        return False

    def update_groups(self, user):
        authinfo = AuthServicesInfo.objects.get_or_create(user=user)[0]
        if authinfo.discourse_enabled:
            update_discourse_groups.delay(user.pk)

    def validate_user(self, user):
        auth = AuthServicesInfo.objects.get_or_create(user=user)[0]
        if auth.discourse_enabled and not self.service_active_for_user(user):
            self.delete_user(user, notify_user=True)

    def update_all_groups(self):
        update_all_discourse_groups.delay()

    def service_enabled_members(self):
        return settings.ENABLE_AUTH_DISCOURSE or False

    def service_enabled_blues(self):
        return settings.ENABLE_BLUE_DISCOURSE or False

    def render_services_ctrl(self, request):
        auth = AuthServicesInfo.objects.get_or_create(user=request.user)[0]
        char = None
        if auth.main_char_id:
            try:
                char = EveCharacter.objects.get(character_id=auth.main_char_id)
            except EveCharacter.DoesNotExist:
                messages.warning(request, "There's a problem with your main character. Please select a new one.")
        return render_to_string(self.service_ctrl_template, {
            'char': char
        }, request=request)


@hooks.register('services_hook')
def register_service():
    return DiscourseService()
