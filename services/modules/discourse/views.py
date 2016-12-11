from __future__ import unicode_literals

from django.conf import settings
from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.shortcuts import render, redirect
from authentication.models import AuthServicesInfo
from authentication.states import MEMBER_STATE, BLUE_STATE, NONE_STATE
from eveonline.models import EveCharacter

from .manager import DiscourseManager
from .tasks import update_discourse_groups

import base64
import hmac
import hashlib

try:
    from urllib import unquote, urlencode
except ImportError: #py3
    from urllib.parse import unquote, urlencode
try:
    from urlparse import parse_qs
except ImportError: #py3
    from urllib.parse import parse_qs

import logging

logger = logging.getLogger(__name__)


@login_required
def discourse_sso(request):

    ## Check if user has access

    auth, c = AuthServicesInfo.objects.get_or_create(user=request.user)
    if not request.user.is_superuser:
        if not settings.ENABLE_AUTH_DISCOURSE and auth.state == MEMBER_STATE:
            messages.error(request, 'Members are not authorized to access Discourse.')
            return redirect('auth_dashboard')
        elif not settings.ENABLE_BLUE_DISCOURSE and auth.state == BLUE_STATE:
            messages.error(request, 'Blues are not authorized to access Discourse.')
            return redirect('auth_dashboard')
        elif auth.state == NONE_STATE:
            messages.error(request, 'You are not authorized to access Discourse.')
            return redirect('auth_dashboard')

    if not auth.main_char_id:
        messages.error(request, "You must have a main character set to access Discourse.")
        return redirect('auth_characters')
    try:
       main_char = EveCharacter.objects.get(character_id=auth.main_char_id)
    except EveCharacter.DoesNotExist:
       messages.error(request, "Your main character is missing a database model. Please select a new one.")
       return redirect('auth_characters')

    payload = request.GET.get('sso')
    signature = request.GET.get('sig')

    if None in [payload, signature]:
        messages.error(request, 'No SSO payload or signature. Please contact support if this problem persists.')
        return redirect('auth_dashboard')

    ## Validate the payload

    try:
        payload = unquote(payload).encode('utf-8')
        decoded = base64.decodestring(payload).decode('utf-8')
        assert 'nonce' in decoded
        assert len(payload) > 0
    except AssertionError:
        messages.error(request, 'Invalid payload. Please contact support if this problem persists.')
        return redirect('auth_dashboard')

    key = str(settings.DISCOURSE_SSO_SECRET).encode('utf-8')
    h = hmac.new(key, payload, digestmod=hashlib.sha256)
    this_signature = h.hexdigest()

    if this_signature != signature:
        messages.error(request, 'Invalid payload. Please contact support if this problem persists.')
        return redirect('auth_dashboard')

    ## Build the return payload

    username = DiscourseManager._sanitize_username(main_char.character_name)

    qs = parse_qs(decoded)
    params = {
        'nonce': qs['nonce'][0],
        'email': request.user.email,
        'external_id': request.user.pk,
        'username': username,
        'name': username,
    }

    if auth.main_char_id:
        params['avatar_url'] = 'https://image.eveonline.com/Character/%s_256.jpg' % auth.main_char_id

    return_payload = base64.encodestring(urlencode(params).encode('utf-8'))
    h = hmac.new(key, return_payload, digestmod=hashlib.sha256)
    query_string = urlencode({'sso': return_payload, 'sig': h.hexdigest()})

    ## Record activation and queue group sync

    if not auth.discourse_enabled:
        auth.discourse_enabled = True
        auth.save()
        update_discourse_groups.apply_async(args=[request.user.pk], countdown=30) # wait 30s for new user creation on Discourse

    ## Redirect back to Discourse

    url = '%s/session/sso_login' % settings.DISCOURSE_URL
    return redirect('%s?%s' % (url, query_string))
