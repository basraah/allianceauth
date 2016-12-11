import logging

from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.shortcuts import render, redirect

from authentication.decorators import members_and_blues
from authentication.managers import AuthServicesInfoManager
from authentication.models import AuthServicesInfo
from authentication.states import BLUE_STATE
from eveonline.managers import EveManager

from services.modules.teamspeak3.manager import Teamspeak3Manager

from .forms import TeamspeakJoinForm
from .tasks import update_teamspeak3_groups, add_ts3_user

logger = logging.getLogger(__name__)


@login_required
@members_and_blues()
def activate_teamspeak3(request):
    logger.debug("activate_teamspeak3 called by user %s" % request.user)

    result = add_ts3_user(request.user)

    # if its empty we failed
    if result[0] is not "":
        AuthServicesInfoManager.update_user_teamspeak3_info(result[0], result[1], request.user)
        logger.debug("Updated authserviceinfo for user %s with TS3 credentials. Updating groups." % request.user)
        logger.info("Successfully activated TS3 for user %s" % request.user)
        messages.success(request, 'Activated TeamSpeak3 account.')
        return redirect("auth_verify_teamspeak3")
    logger.error("Unsuccessful attempt to activate TS3 for user %s" % request.user)
    messages.error(request, 'An error occurred while processing your TeamSpeak3 account.')
    return redirect("auth_services")


@login_required
@members_and_blues()
def verify_teamspeak3(request):
    logger.debug("verify_teamspeak3 called by user %s" % request.user)
    authinfo = AuthServicesInfo.objects.get_or_create(user=request.user)[0]
    if not authinfo.teamspeak3_uid:
        logger.warn("Unable to validate user %s teamspeak: no teamspeak data" % request.user)
        return redirect("auth_services")
    if request.method == "POST":
        form = TeamspeakJoinForm(request.POST)
        if form.is_valid():
            update_teamspeak3_groups.delay(request.user.pk)
            logger.debug("Validated user %s joined TS server" % request.user)
            return redirect("auth_services")
    else:
        form = TeamspeakJoinForm({'username': authinfo.teamspeak3_uid})
    context = {
        'form': form,
        'authinfo': authinfo,
    }
    return render(request, 'registered/teamspeakjoin.html', context=context)


@login_required
@members_and_blues()
def deactivate_teamspeak3(request):
    logger.debug("deactivate_teamspeak3 called by user %s" % request.user)
    authinfo = AuthServicesInfo.objects.get_or_create(user=request.user)[0]
    result = Teamspeak3Manager.delete_user(authinfo.teamspeak3_uid)

    # if false we failed
    if result:
        AuthServicesInfoManager.update_user_teamspeak3_info("", "", request.user)
        logger.info("Successfully deactivated TS3 for user %s" % request.user)
        messages.success(request, 'Deactivated TeamSpeak3 account.')
    else:
        logger.error("Unsuccessful attempt to deactivate TS3 for user %s" % request.user)
        messages.error(request, 'An error occurred while processing your TeamSpeak3 account.')
    return redirect("auth_services")


@login_required
@members_and_blues()
def reset_teamspeak3_perm(request):
    logger.debug("reset_teamspeak3_perm called by user %s" % request.user)
    authinfo = AuthServicesInfo.objects.get_or_create(user=request.user)[0]
    character = EveManager.get_character_by_id(authinfo.main_char_id)
    logger.debug("Deleting TS3 user for user %s" % request.user)
    Teamspeak3Manager.delete_user(authinfo.teamspeak3_uid)

    if authinfo.state == BLUE_STATE:
        logger.debug(
            "Generating new permission key for blue user %s with main character %s" % (request.user, character))
        result = Teamspeak3Manager.generate_new_blue_permissionkey(authinfo.teamspeak3_uid, character.character_name,
                                                                   character.corporation_ticker)
    else:
        logger.debug("Generating new permission key for user %s with main character %s" % (request.user, character))
        result = Teamspeak3Manager.generate_new_permissionkey(authinfo.teamspeak3_uid, character.character_name,
                                                              character.corporation_ticker)

    # if blank we failed
    if result != "":
        AuthServicesInfoManager.update_user_teamspeak3_info(result[0], result[1], request.user)
        logger.debug("Updated authserviceinfo for user %s with TS3 credentials. Updating groups." % request.user)
        update_teamspeak3_groups.delay(request.user)
        logger.info("Successfully reset TS3 permission key for user %s" % request.user)
        messages.success(request, 'Reset TeamSpeak3 permission key.')
    else:
        logger.error("Unsuccessful attempt to reset TS3 permission key for user %s" % request.user)
        messages.error(request, 'An error occurred while processing your TeamSpeak3 account.')
    return redirect("auth_services")
