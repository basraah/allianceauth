from __future__ import unicode_literals

from celery import task
from django.conf import settings
from django.contrib.auth.models import User

from authentication.models import AuthServicesInfo
from eveonline.managers import EveManager
from services.modules.discord.manager import DiscordOAuthManager
from services.tasks import only_one

import logging

logger = logging.getLogger(__name__)


@task(bind=True)
@only_one(key="Discord", timeout=60*5)
def update_discord_groups(self, pk):
    user = User.objects.get(pk=pk)
    logger.debug("Updating discord groups for user %s" % user)
    authserviceinfo = AuthServicesInfo.objects.get(user=user)
    groups = []
    for group in user.groups.all():
        groups.append(str(group.name))
    if len(groups) == 0:
        logger.debug("No syncgroups found for user. Adding empty group.")
        groups.append('empty')
    logger.debug("Updating user %s discord groups to %s" % (user, groups))
    try:
        DiscordOAuthManager.update_groups(authserviceinfo.discord_uid, groups)
    except:
        logger.exception("Discord group sync failed for %s, retrying in 10 mins" % user)
        raise self.retry(countdown=60 * 10)
    logger.debug("Updated user %s discord groups." % user)


@task
def update_all_discord_groups():
    logger.debug("Updating ALL discord groups")
    for user in AuthServicesInfo.objects.exclude(discord_uid__exact=''):
        update_discord_groups.delay(user.user_id)


@task(bind=True)
def update_discord_nickname(self, pk):
    user = User.objects.get(pk=pk)
    logger.debug("Updating discord nickname for user %s" % user)
    authserviceinfo = AuthServicesInfo.objects.get(user=user)
    character = EveManager.get_character_by_id(authserviceinfo.main_char_id)
    logger.debug("Updating user %s discord nickname to %s" % (user, character.character_name))
    try:
        DiscordOAuthManager.update_nickname(authserviceinfo.discord_uid, character.character_name)
    except:
        logger.exception("Discord nickname sync failed for %s, retrying in 10 mins" % user)
        raise self.retry(countdown=60 * 10)
    logger.debug("Updated user %s discord nickname." % user)


@task
def update_all_discord_nicknames():
    logger.debug("Updating ALL discord nicknames")
    for user in AuthServicesInfo.objects.exclude(discord_uid__exact=''):
        update_discord_nickname(user.user_id)


def disable_discord():
    if settings.ENABLE_AUTH_DISCORD:
        logger.warn(
            "ENABLE_AUTH_DISCORD still True, after disabling users will still be able to link Discord accounts")
    if settings.ENABLE_BLUE_DISCORD:
        logger.warn(
            "ENABLE_BLUE_DISCORD still True, after disabling blues will still be able to link Discord accounts")
    for auth in AuthServicesInfo.objects.all():
        if auth.discord_uid:
            logger.info("Clearing %s Discord UID" % auth.user)
            auth.discord_uid = ''
            auth.save()
