from __future__ import unicode_literals

try:
    # Py3
    from unittest import mock
except ImportError:
    # Py2
    import mock

from django.test import TestCase
from alliance_auth.tests.auth_utils import AuthUtils

from eveonline.managers import EveCharacter


class TestEveModels(TestCase):
    def setUp(self):
        self.member = AuthUtils.create_user('auth_member', disconnect_signals=True)
        self.member_character = EveCharacter(
            character_id='95443318',
            character_name='auth_member_character',
            corporation_id='109299958',
            corporation_name='C C P',
            corporation_ticker='-CCP-',
            alliance_id='434243723',
            alliance_name='C C P Alliance',
            api_id='',
            user=self.member,
        )
        self.none_user = AuthUtils.create_user('none_user', disconnect_signals=True)
        self.none_character = EveCharacter(
            character_id='0',
            character_name='none_character',
            corporation_id='1000001',
            corporation_name='Doomheim',
            corporation_ticker='666',
            api_id='',
            user=self.none_user,
        )

    @mock.patch('eveonline.models.settings')
    def test_in_organisation(self, settings):

        # Test alliance level
        settings.STR_CORP_IDS = []
        settings.STR_ALLIANCE_IDS = ['434243723']

        self.assertTrue(self.member_character.in_organisation())
        self.assertFalse(self.none_character.in_organisation())

        # Test corp level
        settings.STR_CORP_IDS = ['109299958']
        settings.STR_ALLIANCE_IDS = []

        self.assertTrue(self.member_character.in_organisation())
        self.assertFalse(self.none_character.in_organisation())
