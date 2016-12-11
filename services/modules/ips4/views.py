from __future__ import unicode_literals

from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.shortcuts import render, redirect

from authentication.decorators import members_and_blues
from authentication.managers import AuthServicesInfoManager
from authentication.models import AuthServicesInfo
from eveonline.managers import EveManager
from services.forms import ServicePasswordForm

from .manager import Ips4Manager

import logging

logger = logging.getLogger(__name__)


@login_required
@members_and_blues()
def activate_ips4(request):
    logger.debug("activate_ips4 called by user %s" % request.user)
    authinfo = AuthServicesInfo.objects.get_or_create(user=request.user)[0]
    # Valid now we get the main characters
    character = EveManager.get_character_by_id(authinfo.main_char_id)
    logger.debug("Adding IPS4 user for user %s with main character %s" % (request.user, character))
    result = Ips4Manager.add_user(character.character_name, request.user.email)
    # if empty we failed
    if result[0] != "":
        AuthServicesInfoManager.update_user_ips4_info(result[0], result[2], request.user)
        logger.debug("Updated authserviceinfo for user %s with IPS4 credentials." % request.user)
        # update_ips4_groups.delay(request.user.pk)
        logger.info("Successfully activated IPS4 for user %s" % request.user)
        messages.success(request, 'Activated IPSuite4 account.')
        credentials = {
            'username': result[0],
            'password': result[1],
        }
        return render(request, 'registered/service_credentials.html',
                      context={'credentials': credentials, 'service': 'IPSuite4'})
    else:
        logger.error("UnSuccessful attempt to activate IPS4 for user %s" % request.user)
        messages.error(request, 'An error occurred while processing your IPSuite4 account.')
    return redirect("auth_services")


@login_required
@members_and_blues()
def reset_ips4_password(request):
    logger.debug("reset_ips4_password called by user %s" % request.user)
    authinfo = AuthServicesInfo.objects.get_or_create(user=request.user)[0]
    result = Ips4Manager.update_user_password(authinfo.ips4_username)
    # false we failed
    if result != "":
        logger.info("Successfully reset IPS4 password for user %s" % request.user)
        messages.success(request, 'Reset IPSuite4 password.')
        credentials = {
            'username': authinfo.ips4_username,
            'password': result,
        }
        return render(request, 'registered/service_credentials.html',
                      context={'credentials': credentials, 'service': 'IPSuite4'})
    else:
        logger.error("Unsuccessful attempt to reset IPS4 password for user %s" % request.user)
        messages.error(request, 'An error occurred while processing your IPSuite4 account.')
    return redirect("auth_services")


@login_required
@members_and_blues()
def set_ips4_password(request):
    logger.debug("set_ips4_password called by user %s" % request.user)
    if request.method == 'POST':
        logger.debug("Received POST request with form.")
        form = ServicePasswordForm(request.POST)
        logger.debug("Form is valid: %s" % form.is_valid())
        if form.is_valid():
            password = form.cleaned_data['password']
            logger.debug("Form contains password of length %s" % len(password))
            authinfo = AuthServicesInfo.objects.get_or_create(user=request.user)[0]
            result = Ips4Manager.update_custom_password(authinfo.ips4_username, plain_password=password)
            if result != "":
                logger.info("Successfully set IPS4 password for user %s" % request.user)
                messages.success(request, 'Set IPSuite4 password.')
            else:
                logger.error("Failed to install custom IPS4 password for user %s" % request.user)
                messages.error(request, 'An error occurred while processing your IPSuite4 account.')
            return redirect('auth_services')
    else:
        logger.debug("Request is not type POST - providing empty form.")
        form = ServicePasswordForm()

    logger.debug("Rendering form for user %s" % request.user)
    context = {'form': form, 'service': 'IPS4'}
    return render(request, 'registered/service_password.html', context=context)


@login_required
@members_and_blues()
def deactivate_ips4(request):
    logger.debug("deactivate_ips4 called by user %s" % request.user)
    authinfo = AuthServicesInfo.objects.get_or_create(user=request.user)[0]
    result = Ips4Manager.delete_user(authinfo.ips4_id)
    if result != "":
        AuthServicesInfoManager.update_user_ips4_info("", "", request.user)
        logger.info("Successfully deactivated IPS4 for user %s" % request.user)
        messages.success(request, 'Deactivated IPSuite4 account.')
    else:
        logger.error("UnSuccessful attempt to deactivate IPS4 for user %s" % request.user)
        messages.error(request, 'An error occurred while processing your IPSuite4 account.')
    return redirect("auth_services")

