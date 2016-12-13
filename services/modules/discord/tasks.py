from __future__ import unicode_literals

import logging

from alliance_auth.celery import app
from django.conf import settings
from django.contrib.auth.models import User
from django.core.exceptions import ObjectDoesNotExist

from eveonline.managers import EveManager
from notifications import notify
from services.modules.discord.manager import DiscordOAuthManager
from services.tasks import only_one
from .models import DiscordUser

logger = logging.getLogger(__name__)


class DiscordTasks:
    def __init__(self):
        pass

    @classmethod
    def add_user(cls, user, code):
        user_id = DiscordOAuthManager.add_user(code)
        if user_id:
            discord_user = DiscordUser()
            discord_user.user = user
            discord_user.uid = user_id
            discord_user.save()
            if settings.DISCORD_SYNC_NAMES:
                update_discord_nickname.delay(user.pk)
            update_discord_groups.delay(user.pk)
            return True
        return False

    @classmethod
    def delete_user(cls, user, notify_user=False):
        if cls.has_account(user):
            logger.debug("User %s has discord account %s. Deleting." % (user, user.discord.uid))
            if DiscordOAuthManager.delete_user(user.discord.uid):
                user.discord.delete()
                if notify_user:
                    notify(user, 'Discord Account Disabled', level='danger')
                return True
        return False

    @classmethod
    def has_account(cls, user):
        """
        Check if the user has an account (has a DiscordUser record)
        :param user: django.contrib.auth.models.User
        :return: bool
        """
        try:
            user.discord
        except ObjectDoesNotExist:
            return False
        else:
            return True

    @classmethod
    def update_discord_groups(cls, pk, task_self=None):
        user = User.objects.get(pk=pk)
        logger.debug("Updating discord groups for user %s" % user)
        if cls.has_account(user):
            groups = []
            for group in user.groups.all():
                groups.append(str(group.name))
            if len(groups) == 0:
                logger.debug("No syncgroups found for user. Adding empty group.")
                groups.append('empty')
            logger.debug("Updating user %s discord groups to %s" % (user, groups))
            try:
                DiscordOAuthManager.update_groups(user.discord.uid, groups)
            except Exception as e:
                if task_self:
                    logger.exception("Discord group sync failed for %s, retrying in 10 mins" % user)
                    raise task_self.retry(countdown=60 * 10)
                else:
                    # Rethrow
                    raise e
            logger.debug("Updated user %s discord groups." % user)
        else:
            logger.debug("User does not have a discord account, skipping")

    @classmethod
    def update_all_discord_groups(cls):
        logger.debug("Updating ALL discord groups")
        for discord_user in DiscordUser.objects.exclude(uid__exact=''):
            update_discord_groups.delay(discord_user.user.pk)

    @classmethod
    def update_discord_nickname(cls, pk, task_self=None):
        user = User.objects.get(pk=pk)
        logger.debug("Updating discord nickname for user %s" % user)
        if cls.has_account(user):
            character = EveManager.get_main_character(user)
            logger.debug("Updating user %s discord nickname to %s" % (user, character.character_name))
            try:
                DiscordOAuthManager.update_nickname(user.discord.uid, character.character_name)
            except Exception as e:
                if task_self:
                    logger.exception("Discord nickname sync failed for %s, retrying in 10 mins" % user)
                    raise task_self.retry(countdown=60 * 10)
                else:
                    # Rethrow
                    raise e
            logger.debug("Updated user %s discord nickname." % user)
        else:
            logger.debug("User %s does not have a discord account" % user)

    @classmethod
    def update_all_discord_nicknames(cls):
        logger.debug("Updating ALL discord nicknames")
        for discord_user in DiscordUser.objects.exclude(uid__exact=''):
            update_discord_nickname.delay(discord_user.user.user_id)

    @classmethod
    def disable_discord(cls):
        if settings.ENABLE_AUTH_DISCORD:
            logger.warn(
                "ENABLE_AUTH_DISCORD still True, after disabling users will still be able to link Discord accounts")
        if settings.ENABLE_BLUE_DISCORD:
            logger.warn(
                "ENABLE_BLUE_DISCORD still True, after disabling blues will still be able to link Discord accounts")
        DiscordUser.objects.all().delete()


@app.task(bind=True)
@only_one(key="Discord", timeout=60 * 5)
def update_discord_groups(self, pk):
    DiscordTasks.update_discord_groups(pk, task_self=self)


@app.task
def update_all_discord_groups():
    DiscordTasks.update_all_discord_groups()


@app.task(bind=True)
def update_discord_nickname(self, pk):
    DiscordTasks.update_discord_nickname(pk, task_self=self)


@app.task
def update_all_discord_nicknames():
    DiscordTasks.update_all_discord_nicknames()
