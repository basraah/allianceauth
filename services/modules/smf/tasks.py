from __future__ import unicode_literals

import logging

from celery import task
from django.contrib.auth.models import User

from authentication.models import AuthServicesInfo
from services.modules.smf.manager import smfManager

logger = logging.getLogger(__name__)


@task(bind=True)
def update_smf_groups(self, pk):
    user = User.objects.get(pk=pk)
    logger.debug("Updating smf groups for user %s" % user)
    authserviceinfo = AuthServicesInfo.objects.get(user=user)
    groups = []
    for group in user.groups.all():
        groups.append(str(group.name))
    if len(groups) == 0:
        groups.append('empty')
    logger.debug("Updating user %s smf groups to %s" % (user, groups))
    try:
        smfManager.update_groups(authserviceinfo.smf_username, groups)
    except:
        logger.exception("smf group sync failed for %s, retrying in 10 mins" % user)
        raise self.retry(countdown=60 * 10)
    logger.debug("Updated user %s smf groups." % user)


@task
def update_all_smf_groups():
    logger.debug("Updating ALL smf groups")
    for user in AuthServicesInfo.objects.exclude(smf_username__exact=''):
        update_smf_groups.delay(user.user_id)
