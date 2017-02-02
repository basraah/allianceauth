from __future__ import unicode_literals

import logging

from alliance_auth.celeryapp import app
from django.conf import settings
from django.core.exceptions import ObjectDoesNotExist
from django.contrib.auth.models import User
from notifications import notify

from services.modules.openfire.manager import OpenfireManager

from .models import OpenfireUser

logger = logging.getLogger(__name__)


class OpenfireTasks:
    def __init__(self):
        pass

    @classmethod
    def delete_user(cls, user, notify_user=False):
        if cls.has_account(user):
            logger.debug("User %s has jabber account %s. Deleting." % (user, user.openfire.username))
            OpenfireManager.delete_user(user.openfire.username)
            user.openfire.delete()
            if notify_user:
                notify(user, 'Jabber Account Disabled', level='danger')
            return True
        return False

    @staticmethod
    def has_account(user):
        try:
            return user.openfire.username != ''
        except ObjectDoesNotExist:
            return False

    @staticmethod
    def disable_jabber():
        logging.debug("Deleting all Openfire users")
        OpenfireUser.objects.all().delete()

    @staticmethod
    @app.task(bind=True)
    def update_groups(self, pk):
        user = User.objects.get(pk=pk)
        logger.debug("Updating jabber groups for user %s" % user)
        if OpenfireTasks.has_account(user):
            groups = []
            for group in user.groups.all():
                groups.append(str(group.name))
            if len(groups) == 0:
                groups.append('empty')
            logger.debug("Updating user %s jabber groups to %s" % (user, groups))
            try:
                OpenfireManager.update_user_groups(user.openfire.username, groups)
            except:
                logger.exception("Jabber group sync failed for %s, retrying in 10 mins" % user)
                raise self.retry(countdown=60 * 10)
            logger.debug("Updated user %s jabber groups." % user)
        else:
            logger.debug("User does not have an openfire account")

    @staticmethod
    @app.task
    def update_all_groups():
        logger.debug("Updating ALL jabber groups")
        for openfire_user in OpenfireUser.objects.exclude(username__exact=''):
            OpenfireTasks.update_groups.delay(openfire_user.user.pk)
