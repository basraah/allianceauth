from __future__ import unicode_literals

from django.apps import AppConfig


class ServicesConfig(AppConfig):
    name = 'allianceauth.services'
    label = 'services'

    def ready(self):
        pass