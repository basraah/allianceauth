from __future__ import unicode_literals

import logging

from django.conf import settings
from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.contrib.auth.decorators import user_passes_test
from django.shortcuts import redirect

from authentication.decorators import members_and_blues
from authentication.managers import AuthServicesInfoManager
from authentication.models import AuthServicesInfo
from services.modules.discord.manager import DiscordOAuthManager
from .tasks import update_discord_groups
from .tasks import update_discord_nickname
from services.views import superuser_test

logger = logging.getLogger(__name__)


@login_required
@members_and_blues()
def deactivate_discord(request):
    logger.debug("deactivate_discord called by user %s" % request.user)
    authinfo = AuthServicesInfo.objects.get_or_create(user=request.user)[0]
    result = DiscordOAuthManager.delete_user(authinfo.discord_uid)
    if result:
        AuthServicesInfoManager.update_user_discord_info("", request.user)
        logger.info("Successfully deactivated discord for user %s" % request.user)
        messages.success(request, 'Deactivated Discord account.')
    else:
        logger.error("UnSuccessful attempt to deactivate discord for user %s" % request.user)
        messages.error(request, 'An error occurred while processing your Discord account.')
    return redirect("auth_services")


@login_required
@members_and_blues()
def reset_discord(request):
    logger.debug("reset_discord called by user %s" % request.user)
    authinfo = AuthServicesInfo.objects.get_or_create(user=request.user)[0]
    result = DiscordOAuthManager.delete_user(authinfo.discord_uid)
    if result:
        AuthServicesInfoManager.update_user_discord_info("", request.user)
        logger.info("Successfully deleted discord user for user %s - forwarding to discord activation." % request.user)
        return redirect("auth_activate_discord")
    logger.error("Unsuccessful attempt to reset discord for user %s" % request.user)
    messages.error(request, 'An error occurred while processing your Discord account.')
    return redirect("auth_services")


@login_required
@members_and_blues()
def activate_discord(request):
    logger.debug("activate_discord called by user %s" % request.user)
    return redirect(DiscordOAuthManager.generate_oauth_redirect_url())


@login_required
@members_and_blues()
def discord_callback(request):
    logger.debug("Received Discord callback for activation of user %s" % request.user)
    code = request.GET.get('code', None)
    if not code:
        logger.warn("Did not receive OAuth code from callback of user %s" % request.user)
        return redirect("auth_services")
    user_id = DiscordOAuthManager.add_user(code)
    if user_id:
        AuthServicesInfoManager.update_user_discord_info(user_id, request.user)
        if settings.DISCORD_SYNC_NAMES:
            update_discord_nickname.delay(request.user.pk)
        update_discord_groups.delay(request.user.pk)
        logger.info("Successfully activated Discord for user %s" % request.user)
        messages.success(request, 'Activated Discord account.')
    else:
        logger.error("Failed to activate Discord for user %s" % request.user)
        messages.error(request, 'An error occurred while processing your Discord account.')
    return redirect("auth_services")


@login_required
@user_passes_test(superuser_test)
def discord_add_bot(request):
    return redirect(DiscordOAuthManager.generate_bot_add_url())

