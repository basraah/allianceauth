from __future__ import unicode_literals

import logging

from celery import task
from celery.task import periodic_task
from celery.task.schedules import crontab
from django.conf import settings
from django.contrib.auth.models import User

from eveonline.managers import EveManager
from eveonline.models import EveAllianceInfo
from authentication.states import BLUE_STATE

from authentication.models import AuthServicesInfo
from .util.ts3 import TeamspeakError
from .manager import Teamspeak3Manager
from .models import AuthTS, TSgroup, UserTSgroup

logger = logging.getLogger(__name__)


def add_ts3_user(user):
    authinfo = AuthServicesInfo.objects.get_or_create(user=user)[0]
    character = EveManager.get_character_by_id(authinfo.main_char_id)
    ticker = character.corporation_ticker

    if authinfo.state == BLUE_STATE:
        logger.debug("Adding TS3 user for blue user %s with main character %s" % (user, character))
        # Blue members should have alliance ticker (if in alliance)
        if EveAllianceInfo.objects.filter(alliance_id=character.alliance_id).exists():
            alliance = EveAllianceInfo.objects.filter(alliance_id=character.alliance_id)[0]
            ticker = alliance.alliance_ticker
        result = Teamspeak3Manager.add_blue_user(character.character_name, ticker)
    else:
        logger.debug("Adding TS3 user for user %s with main character %s" % (user, character))
        result = Teamspeak3Manager.add_user(character.character_name, ticker)

    return result


@periodic_task(run_every=crontab(minute="*/30"))
def run_ts3_group_update():
    if settings.ENABLE_AUTH_TEAMSPEAK3 or settings.ENABLE_BLUE_TEAMSPEAK3:
        logger.debug("TS3 installed. Syncing local group objects.")
        Teamspeak3Manager._sync_ts_group_db()


def disable_teamspeak():
    if settings.ENABLE_AUTH_TEAMSPEAK3:
        logger.warn(
            "ENABLE_AUTH_TEAMSPEAK3 still True, after disabling users will still be able to create teamspeak accounts")
    if settings.ENABLE_BLUE_TEAMSPEAK3:
        logger.warn(
            "ENABLE_BLUE_TEAMSPEAK3 still True, after disabling blues will still be able to create teamspeak accounts")
    for auth in AuthServicesInfo.objects.all():
        if auth.teamspeak3_uid:
            logger.info("Clearing %s Teamspeak3 UID" % auth.user)
            auth.teamspeak3_uid = ''
            auth.save()
        if auth.teamspeak3_perm_key:
            logger.info("Clearing %s Teamspeak3 permission key" % auth.user)
            auth.teamspeak3_perm_key = ''
            auth.save()
    logger.info("Deleting all UserTSgroup models")
    UserTSgroup.objects.all().delete()
    logger.info("Deleting all AuthTS models")
    AuthTS.objects.all().delete()
    logger.info("Deleting all TSgroup models")
    TSgroup.objects.all().delete()
    logger.info("Teamspeak3 disabled")


@task(bind=True)
def update_teamspeak3_groups(self, pk):
    user = User.objects.get(pk=pk)
    logger.debug("Updating user %s teamspeak3 groups" % user)
    usergroups = user.groups.all()
    authserviceinfo = AuthServicesInfo.objects.get(user=user)
    groups = {}
    for usergroup in usergroups:
        filtered_groups = AuthTS.objects.filter(auth_group=usergroup)
        if filtered_groups:
            for filtered_group in filtered_groups:
                for ts_group in filtered_group.ts_group.all():
                    groups[ts_group.ts_group_name] = ts_group.ts_group_id
    logger.debug("Updating user %s teamspeak3 groups to %s" % (user, groups))
    try:
        Teamspeak3Manager.update_groups(authserviceinfo.teamspeak3_uid, groups)
        logger.debug("Updated user %s teamspeak3 groups." % user)
    except TeamspeakError as e:
        logger.error("Error occured while syncing TS groups for %s: %s" % (user, str(e)))
        raise self.retry(countdown=60*10)


@task
def update_all_teamspeak3_groups():
    logger.debug("Updating ALL teamspeak3 groups")
    for user in AuthServicesInfo.objects.exclude(teamspeak3_uid__exact=''):
        update_teamspeak3_groups.delay(user.user_id)
