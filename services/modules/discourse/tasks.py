from __future__ import unicode_literals

from celery import task
from django.contrib.auth.models import User

from authentication.models import AuthServicesInfo
from services.tasks import only_one

from .manager import DiscourseManager

import logging

logger = logging.getLogger(__name__)


@task(bind=True)
@only_one(key="Discourse", timeout=60*5)
def update_discourse_groups(self, pk):
    user = User.objects.get(pk=pk)
    logger.debug("Updating discourse groups for user %s" % user)
    try:
        DiscourseManager.update_groups(user)
    except:
        logger.warn("Discourse group sync failed for %s, retrying in 10 mins" % user)
        raise self.retry(countdown=60 * 10)
    logger.debug("Updated user %s discourse groups." % user)


@task
def update_all_discourse_groups():
    logger.debug("Updating ALL discourse groups")
    for user in AuthServicesInfo.objects.exclude(discourse_username__exact=''):
        update_discourse_groups.delay(user.user_id)
