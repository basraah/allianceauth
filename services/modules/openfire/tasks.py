from __future__ import unicode_literals

import logging

import redis
from celery import task
from django.conf import settings
from django.contrib.auth.models import User

from authentication.models import AuthServicesInfo
from services.modules.openfire.manager import OpenfireManager

REDIS_CLIENT = redis.Redis()

logger = logging.getLogger(__name__)


def disable_jabber():
    if settings.ENABLE_AUTH_JABBER:
        logger.warn("ENABLE_AUTH_JABBER still True, after disabling users will still be able to create jabber accounts")
    if settings.ENABLE_BLUE_JABBER:
        logger.warn("ENABLE_BLUE_JABBER still True, after disabling blues will still be able to create jabber accounts")
    for auth in AuthServicesInfo.objects.all():
        if auth.jabber_username:
            logger.info("Clearing %s jabber username" % auth.user)
            auth.jabber_username = ''
            auth.save()


@task(bind=True)
def update_jabber_groups(self, pk):
    user = User.objects.get(pk=pk)
    logger.debug("Updating jabber groups for user %s" % user)
    authserviceinfo = AuthServicesInfo.objects.get(user=user)
    groups = []
    for group in user.groups.all():
        groups.append(str(group.name))
    if len(groups) == 0:
        groups.append('empty')
    logger.debug("Updating user %s jabber groups to %s" % (user, groups))
    try:
        OpenfireManager.update_user_groups(authserviceinfo.jabber_username, groups)
    except:
        logger.exception("Jabber group sync failed for %s, retrying in 10 mins" % user)
        raise self.retry(countdown=60 * 10)
    logger.debug("Updated user %s jabber groups." % user)


@task
def update_all_jabber_groups():
    logger.debug("Updating ALL jabber groups")
    for user in AuthServicesInfo.objects.exclude(jabber_username__exact=''):
        update_jabber_groups.delay(user.user_id)
