from __future__ import unicode_literals

import logging

from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.shortcuts import render, redirect

from authentication.decorators import members_and_blues
from authentication.managers import AuthServicesInfoManager
from authentication.models import AuthServicesInfo
from eveonline.managers import EveManager
from services.forms import ServicePasswordForm
from .manager import XenForoManager

logger = logging.getLogger(__name__)

@login_required
@members_and_blues()
def activate_xenforo_forum(request):
    logger.debug("activate_xenforo_forum called by user %s" % request.user)
    authinfo = AuthServicesInfo.objects.get_or_create(user=request.user)[0]
    character = EveManager.get_character_by_id(authinfo.main_char_id)
    logger.debug("Adding XenForo user for user %s with main character %s" % (request.user, character))
    result = XenForoManager.add_user(character.character_name, request.user.email)
    # Based on XenAPI's response codes
    if result['response']['status_code'] == 200:
        logger.info("Updated authserviceinfo for user %s with XenForo credentials. Updating groups." % request.user)
        AuthServicesInfoManager.update_user_xenforo_info(result['username'], request.user)
        messages.success(request, 'Activated XenForo account.')
        credentials = {
            'username': result['username'],
            'password': result['password'],
        }
        return render(request, 'registered/service_credentials.html',
                      context={'credentials': credentials, 'service': 'XenForo'})

    else:
        logger.error("UnSuccessful attempt to activate xenforo for user %s" % request.user)
        messages.error(request, 'An error occurred while processing your XenForo account.')
    return redirect("auth_services")


@login_required
@members_and_blues()
def deactivate_xenforo_forum(request):
    logger.debug("deactivate_xenforo_forum called by user %s" % request.user)
    authinfo = AuthServicesInfo.objects.get_or_create(user=request.user)[0]
    result = XenForoManager.disable_user(authinfo.xenforo_username)
    if result.status_code == 200:
        AuthServicesInfoManager.update_user_xenforo_info("", request.user)
        logger.info("Successfully deactivated XenForo for user %s" % request.user)
        messages.success(request, 'Deactivated XenForo account.')
    else:
        messages.error(request, 'An error occurred while processing your XenForo account.')
    return redirect("auth_services")


@login_required
@members_and_blues()
def reset_xenforo_password(request):
    logger.debug("reset_xenforo_password called by user %s" % request.user)
    authinfo = AuthServicesInfo.objects.get_or_create(user=request.user)[0]
    result = XenForoManager.reset_password(authinfo.xenforo_username)
    # Based on XenAPI's response codes
    if result['response']['status_code'] == 200:
        logger.info("Successfully reset XenForo password for user %s" % request.user)
        messages.success(request, 'Reset XenForo account password.')
        credentials = {
            'username': authinfo.xenforo_username,
            'password': result['password'],
        }
        return render(request, 'registered/service_credentials.html',
                      context={'credentials': credentials, 'service': 'XenForo'})
    else:
        logger.error("Unsuccessful attempt to reset XenForo password for user %s" % request.user)
        messages.error(request, 'An error occurred while processing your XenForo account.')
    return redirect("auth_services")


@login_required
@members_and_blues()
def set_xenforo_password(request):
    logger.debug("set_xenforo_password called by user %s" % request.user)
    if request.method == 'POST':
        logger.debug("Received POST request with form.")
        form = ServicePasswordForm(request.POST)
        logger.debug("Form is valid: %s" % form.is_valid())
        if form.is_valid():
            password = form.cleaned_data['password']
            logger.debug("Form contains password of length %s" % len(password))
            authinfo = AuthServicesInfo.objects.get_or_create(user=request.user)[0]
            result = XenForoManager.update_user_password(authinfo.xenforo_username, password)
            if result['response']['status_code'] == 200:
                logger.info("Successfully reset XenForo password for user %s" % request.user)
                messages.success(request, 'Changed XenForo password.')
            else:
                logger.error("Failed to install custom XenForo password for user %s" % request.user)
                messages.error(request, 'An error occurred while processing your XenForo account.')
            return redirect('auth_services')
    else:
        logger.debug("Request is not type POST - providing empty form.")
        form = ServicePasswordForm()

    logger.debug("Rendering form for user %s" % request.user)
    context = {'form': form, 'service': 'Forum'}
    return render(request, 'registered/service_password.html', context=context)
