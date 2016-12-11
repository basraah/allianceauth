from __future__ import unicode_literals

from django.conf import settings

from authentication.models import AuthServicesInfo


import logging

logger = logging.getLogger(__name__)


def disable_market():
    if settings.ENABLE_AUTH_MARKET:
        logger.warn("ENABLE_AUTH_MARKET still True, after disabling users will still be able to activate Market accounts")
    if settings.ENABLE_BLUE_MARKET:
        logger.warn("ENABLE_BLUE_MARKET still True, after disabling blues will still be able to activate Market accounts")
    for auth in AuthServicesInfo.objects.all():
        if auth.market_username:
            logger.info("Clearing %s market username" % auth.user)
            auth.market_username = ''
            auth.save()
