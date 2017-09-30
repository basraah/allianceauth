
from django.test import TestCase
from django.contrib.auth.models import Group
from django.db.models.signals import pre_save, post_save, pre_delete, m2m_changed

from unittest import mock
from allianceauth.tests.auth_utils import AuthUtils

from allianceauth.eveonline.models import EveCharacter, EveCorporationInfo, EveAllianceInfo

from ..models import AutogroupsConfig, get_users_for_state

from . import patch


class SignalsTestCase(TestCase):
    def setUp(self):
        self.member = AuthUtils.create_member('test user')

        state = AuthUtils.get_member_state()

        self.alliance = EveAllianceInfo.objects.create(
            alliance_id='3456',
            alliance_name='alliance name',
            alliance_ticker='TIKR',
            executor_corp_id='2345',
        )

        self.corp = EveCorporationInfo.objects.create(
            corporation_id='2345',
            corporation_name='corp name',
            corporation_ticker='TIKK',
            member_count=10,
            alliance=self.alliance,
        )

        state.member_alliances.add(self.alliance)
        state.member_corporations.add(self.corp)

    @patch
    def test_profile_state_change(self):
        pass
