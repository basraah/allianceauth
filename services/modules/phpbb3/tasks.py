from __future__ import unicode_literals

from celery import task
from django.conf import settings
from django.contrib.auth.models import User

from authentication.models import AuthServicesInfo

from .manager import Phpbb3Manager

import logging

logger = logging.getLogger(__name__)


@task(bind=True)
def update_forum_groups(self, pk):
    user = User.objects.get(pk=pk)
    logger.debug("Updating forum groups for user %s" % user)
    authserviceinfo = AuthServicesInfo.objects.get(user=user)
    groups = []
    for group in user.groups.all():
        groups.append(str(group.name))
    if len(groups) == 0:
        groups.append('empty')
    logger.debug("Updating user %s forum groups to %s" % (user, groups))
    try:
        Phpbb3Manager.update_groups(authserviceinfo.forum_username, groups)
    except:
        logger.exception("Phpbb group sync failed for %s, retrying in 10 mins" % user)
        raise self.retry(countdown=60 * 10)
    logger.debug("Updated user %s forum groups." % user)


@task
def update_all_forum_groups():
    logger.debug("Updating ALL forum groups")
    for user in AuthServicesInfo.objects.exclude(forum_username__exact=''):
        update_forum_groups.delay(user.user_id)


def disable_forum():
    if settings.ENABLE_AUTH_FORUM:
        logger.warn("ENABLE_AUTH_FORUM still True, after disabling users will still be able to create forum accounts")
    if settings.ENABLE_BLUE_FORUM:
        logger.warn("ENABLE_BLUE_FORUM still True, after disabling blues will still be able to create forum accounts")
    for auth in AuthServicesInfo.objects.all():
        if auth.forum_username:
            logger.info("Clearing %s forum username" % auth.user)
            auth.forum_username = ''
            auth.save()
