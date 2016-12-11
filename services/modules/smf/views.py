from __future__ import unicode_literals

from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.shortcuts import render, redirect

from authentication.decorators import members_and_blues
from authentication.managers import AuthServicesInfoManager
from authentication.models import AuthServicesInfo
from eveonline.managers import EveManager
from services.forms import ServicePasswordForm

from .manager import smfManager
from .tasks import update_smf_groups

import logging

logger = logging.getLogger(__name__)


@login_required
@members_and_blues()
def activate_smf(request):
    logger.debug("activate_smf called by user %s" % request.user)
    authinfo = AuthServicesInfo.objects.get_or_create(user=request.user)[0]
    # Valid now we get the main characters
    character = EveManager.get_character_by_id(authinfo.main_char_id)
    logger.debug("Adding smf user for user %s with main character %s" % (request.user, character))
    result = smfManager.add_user(character.character_name, request.user.email, ['Member'], authinfo.main_char_id)
    # if empty we failed
    if result[0] != "":
        AuthServicesInfoManager.update_user_smf_info(result[0], request.user)
        logger.debug("Updated authserviceinfo for user %s with smf credentials. Updating groups." % request.user)
        update_smf_groups.delay(request.user.pk)
        logger.info("Successfully activated smf for user %s" % request.user)
        messages.success(request, 'Activated SMF account.')
        credentials = {
            'username': result[0],
            'password': result[1],
        }
        return render(request, 'registered/service_credentials.html',
                      context={'credentials': credentials, 'service': 'SMF'})
    else:
        logger.error("UnSuccessful attempt to activate smf for user %s" % request.user)
        messages.error(request, 'An error occurred while processing your SMF account.')
    return redirect("auth_services")


@login_required
@members_and_blues()
def deactivate_smf(request):
    logger.debug("deactivate_smf called by user %s" % request.user)
    authinfo = AuthServicesInfo.objects.get_or_create(user=request.user)[0]
    result = smfManager.disable_user(authinfo.smf_username)
    # false we failed
    if result:
        AuthServicesInfoManager.update_user_smf_info("", request.user)
        logger.info("Successfully deactivated smf for user %s" % request.user)
        messages.success(request, 'Deactivated SMF account.')
    else:
        logger.error("UnSuccessful attempt to activate smf for user %s" % request.user)
        messages.error(request, 'An error occurred while processing your SMF account.')
    return redirect("auth_services")


@login_required
@members_and_blues()
def reset_smf_password(request):
    logger.debug("reset_smf_password called by user %s" % request.user)
    authinfo = AuthServicesInfo.objects.get_or_create(user=request.user)[0]
    result = smfManager.update_user_password(authinfo.smf_username, authinfo.main_char_id)
    # false we failed
    if result != "":
        logger.info("Successfully reset smf password for user %s" % request.user)
        messages.success(request, 'Reset SMF password.')
        credentials = {
            'username': authinfo.smf_username,
            'password': result,
        }
        return render(request, 'registered/service_credentials.html',
                      context={'credentials': credentials, 'service': 'SMF'})
    else:
        logger.error("Unsuccessful attempt to reset smf password for user %s" % request.user)
        messages.error(request, 'An error occurred while processing your SMF account.')
    return redirect("auth_services")


@login_required
@members_and_blues()
def set_smf_password(request):
    logger.debug("set_smf_password called by user %s" % request.user)
    if request.method == 'POST':
        logger.debug("Received POST request with form.")
        form = ServicePasswordForm(request.POST)
        logger.debug("Form is valid: %s" % form.is_valid())
        if form.is_valid():
            password = form.cleaned_data['password']
            logger.debug("Form contains password of length %s" % len(password))
            authinfo = AuthServicesInfo.objects.get_or_create(user=request.user)[0]
            result = smfManager.update_user_password(authinfo.smf_username, authinfo.main_char_id, password=password)
            if result != "":
                logger.info("Successfully set smf password for user %s" % request.user)
                messages.success(request, 'Set SMF password.')
            else:
                logger.error("Failed to install custom smf password for user %s" % request.user)
                messages.error(request, 'An error occurred while processing your SMF account.')
            return redirect("auth_services")
    else:
        logger.debug("Request is not type POST - providing empty form.")
        form = ServicePasswordForm()

    logger.debug("Rendering form for user %s" % request.user)
    context = {'form': form, 'service': 'SMF'}
    return render(request, 'registered/service_password.html', context=context)
