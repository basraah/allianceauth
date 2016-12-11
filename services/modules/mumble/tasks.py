from __future__ import unicode_literals

from celery import task
from django.conf import settings
from django.contrib.auth.models import User

from authentication.models import AuthServicesInfo

from .models import MumbleUser
from .manager import MumbleManager

import logging

logger = logging.getLogger(__name__)


def disable_mumble():
    if settings.ENABLE_AUTH_MUMBLE:
        logger.warn("ENABLE_AUTH_MUMBLE still True, after disabling users will still be able to create mumble accounts")
    if settings.ENABLE_BLUE_MUMBLE:
        logger.warn("ENABLE_BLUE_MUMBLE still True, after disabling blues will still be able to create mumble accounts")
    for auth in AuthServicesInfo.objects.all():
        if auth.mumble_username:
            logger.info("Clearing %s mumble username" % auth.user)
            auth.mumble_username = ''
            auth.save()
    logger.info("Deleting all MumbleUser models")
    MumbleUser.objects.all().delete()


@task(bind=True)
def update_mumble_groups(self, pk):
    user = User.objects.get(pk=pk)
    logger.debug("Updating mumble groups for user %s" % user)
    authserviceinfo = AuthServicesInfo.objects.get(user=user)
    groups = []
    for group in user.groups.all():
        groups.append(str(group.name))
    if len(groups) == 0:
        groups.append('empty')
    logger.debug("Updating user %s mumble groups to %s" % (user, groups))
    try:
        MumbleManager.update_groups(authserviceinfo.mumble_username, groups)
    except:
        logger.exception("Mumble group sync failed for %s, retrying in 10 mins" % user)
        raise self.retry(countdown=60 * 10)
    logger.debug("Updated user %s mumble groups." % user)


@task
def update_all_mumble_groups():
    logger.debug("Updating ALL mumble groups")
    for user in AuthServicesInfo.objects.exclude(mumble_username__exact=''):
        update_mumble_groups.delay(user.user_id)
