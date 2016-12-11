from __future__ import unicode_literals

from celery import task
from django.conf import settings
from django.contrib.auth.models import User

from authentication.models import AuthServicesInfo
from eveonline.managers import EveManager

from .manager import IPBoardManager

import logging

logger = logging.getLogger(__name__)


@task(bind=True)
def update_ipboard_groups(self, pk):
    user = User.objects.get(pk=pk)
    logger.debug("Updating user %s ipboard groups." % user)
    authserviceinfo = AuthServicesInfo.objects.get(user=user)
    groups = []
    for group in user.groups.all():
        groups.append(str(group.name))
    if len(groups) == 0:
        groups.append('empty')
    logger.debug("Updating user %s ipboard groups to %s" % (user, groups))
    try:
        IPBoardManager.update_groups(authserviceinfo.ipboard_username, groups)
    except:
        logger.exception("IPBoard group sync failed for %s, retrying in 10 mins" % user)
        raise self.retry(countdown=60 * 10)
    logger.debug("Updated user %s ipboard groups." % user)


@task
def update_all_ipboard_groups():
    logger.debug("Updating ALL ipboard groups")
    for user in AuthServicesInfo.objects.exclude(ipboard_username__exact=''):
        update_ipboard_groups.delay(user.user_id)


def disable_ipboard():
    if settings.ENABLE_AUTH_IPBOARD:
        logger.warn(
            "ENABLE_AUTH_IPBOARD still True, after disabling users will still be able to create IPBoard accounts")
    if settings.ENABLE_BLUE_IPBOARD:
        logger.warn(
            "ENABLE_BLUE_IPBOARD still True, after disabling blues will still be able to create IPBoard accounts")
    for auth in AuthServicesInfo.objects.all():
        if auth.ipboard_username:
            logger.info("Clearing %s ipboard username" % auth.user)
            auth.ipboard_username = ''
            auth.save()
