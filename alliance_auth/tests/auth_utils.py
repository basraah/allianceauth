from __future__ import unicode_literals

from django.db.models.signals import m2m_changed, pre_save
from django.contrib.auth.models import User

from services.signals import m2m_changed_user_groups, pre_save_user

from authentication.tasks import make_member, make_blue
from authentication.models import AuthServicesInfo
from authentication.states import MEMBER_STATE, BLUE_STATE, NONE_STATE

from eveonline.models import EveCharacter


class AuthUtils:
    def __init__(self):
        pass

    @staticmethod
    def _create_user(username):
        return User.objects.create(username=username)

    @classmethod
    def create_user(cls, username, disconnect_signals=False):
        if disconnect_signals:
            cls.disconnect_signals()
        user = cls._create_user(username)
        AuthServicesInfo.objects.get_or_create(user=user, defaults={'state': NONE_STATE})
        if disconnect_signals:
            cls.connect_signals()
        return user

    @classmethod
    def create_member(cls, username):
        cls.disconnect_signals()
        user = cls._create_user(username)
        make_member(AuthServicesInfo.objects.get_or_create(user=user, defaults={'state': MEMBER_STATE})[0])
        cls.connect_signals()
        return user

    @classmethod
    def create_blue(cls, username):
        cls.disconnect_signals()
        user = cls._create_user(username)
        make_blue(AuthServicesInfo.objects.get_or_create(user=user, defaults={'state': BLUE_STATE})[0])
        cls.connect_signals()
        return user

    @classmethod
    def disconnect_signals(cls):
        m2m_changed.disconnect(m2m_changed_user_groups, sender=User.groups.through)
        pre_save.disconnect(pre_save_user, sender=User)

    @classmethod
    def connect_signals(cls):
        m2m_changed.connect(m2m_changed_user_groups, sender=User.groups.through)
        pre_save.connect(pre_save_user, sender=User)

    @classmethod
    def add_main_character(cls, user, name, character_id, corp_id='', corp_name='', corp_ticker='', alliance_id='',
                           alliance_name=''):
        EveCharacter.objects.create(
            character_id=character_id,
            character_name=name,
            corporation_id=corp_id,
            corporation_name=corp_name,
            corporation_ticker=corp_ticker,
            alliance_id=alliance_id,
            alliance_name=alliance_name,
            api_id='1234',
            user=user
        )
        AuthServicesInfo.objects.update_or_create(user=user, defaults={'main_char_id': character_id})