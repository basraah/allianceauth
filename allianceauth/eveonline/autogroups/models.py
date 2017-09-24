import logging
from django.db import models, transaction
from django.contrib.auth.models import Group, User

from allianceauth.authentication.models import State
from allianceauth.eveonline.models import EveCorporationInfo, EveAllianceInfo

logger = logging.getLogger(__name__)


class AutogroupsConfigManager(models.Manager):
    def update_groups_for_state(self, state: State):
        """
        Update all the Group memberships for the users
        who have State
        :param state: State to update for
        :return:
        """
        users = User.objects.select_related('profile').fetch_related('profile__main_character')\
            .filter(profile__state__pk=state.pk)
        for config in self.filter(state=state):
            for user in users:
                config.update_group_membership(user)

    def update_groups_for_user(self, state: State, user: User):
        """
        Update the Group memberships for the given users state
        :param user: User to update for
        :param state: State to update user for
        :return:
        """
        for config in self.filter(state=state):
                config.update_group_membership(user)


class AutogroupsConfig(models.Model):
    OPT_TICKER = 'ticker'
    OPT_NAME = 'name'
    NAME_OPTIONS = (
        (OPT_TICKER, 'Ticker'),
        (OPT_NAME, 'Full name'),
    )

    state = models.ManyToManyField(State, related_name='autogroups')

    corp_groups = models.BooleanField(default=False,
                                      help_text="Setting this to false will delete all the created groups.")
    corp_group_prefix = models.CharField(max_length=50, default='Corp ', blank=True)
    corp_name_source = models.CharField(max_length=20, choices=NAME_OPTIONS, default=OPT_NAME)

    alliance_groups = models.BooleanField(default=False,
                                          help_text="Setting this to false will delete all the created groups.")
    alliance_group_prefix = models.CharField(max_length=50, default='Alliance ', blank=True)
    alliance_name_source = models.CharField(max_length=20, choices=NAME_OPTIONS, default=OPT_NAME)

    corp_managed_groups = models.ManyToManyField(
        Group, through='ManagedCorpGroup', related_name='corp_managed_config',
        help_text='A list of corporation groups created and maintained by this AutogroupConfig. '
                  'You should not edit this list unless you know what you\'re doing.')

    alliance_managed_groups = models.ManyToManyField(
        Group, through='ManagedAllianceGroup', related_name='alliance_managed_config',
        help_text='A list of alliance groups created and maintained by this AutogroupConfig. '
                  'You should not edit this list unless you know what you\'re doing.')

    replace_spaces = models.BooleanField(default=False)
    replace_spaces_with = models.CharField(
        max_length=10, default='', blank=True,
        help_text='Any spaces in the group name will be replaced with this.')

    objects = AutogroupsConfigManager()

    def __init__(self, *args, **kwargs):
        super(AutogroupsConfig, self).__init__(*args, **kwargs)
        self._alliance_group_cache = dict()
        self._corp_group_cache = dict()

    def update_group_membership(self, user: User):
        self.update_alliance_group_membership(user)
        self.update_corp_group_membership(user)

    def update_alliance_group_membership(self, user: User):
        with transaction.atomic():
            self.remove_user_from_alliance_groups(user)  # TODO more efficient way of doing this
            if not self.alliance_groups:
                return
            try:
                alliance = user.profile.main_character.alliance
                if alliance is None:
                    return
                group = self.get_alliance_group(user.profile.main_character.alliance)

                if not user.groups.filter(pk=group.pk).exists():
                    user.groups.add(group)
            except EveAllianceInfo.DoesNotExist:
                logger.warning('User {} main characters Alliance does not exist in the database.'
                               ' Group membership not updated'.format(user))

    def update_corp_group_membership(self, user: User):
        with transaction.atomic():
            self.remove_user_from_corp_groups(user)  # TODO more efficient way of doing this
            if not self.corp_groups:
                return
            try:
                corp = user.profile.main_character.corporation
                group = self.get_corp_group(corp)

                if not user.groups.filter(pk=group.pk).exists():
                    user.groups.add(group)
            except EveCorporationInfo.DoesNotExist:
                logger.warning('User {} main characters Corporation does not exist in the database.'
                               ' Group membership not updated'.format(user))

    def remove_user_from_alliance_groups(self, user: User):
        user.groups.intersect(self.alliance_managed_groups.groups.all()).remove()

    def remove_user_from_corp_groups(self, user: User):
        user.groups.intersect(self.corp_managed_groups.groups.all()).remove()

    def get_alliance_group(self, alliance: EveAllianceInfo) -> Group:
        if alliance.alliance_id not in self._alliance_group_cache:
            self._alliance_group_cache[alliance.alliance_id] = self.create_alliance_group(alliance)
        return self._alliance_group_cache[alliance.alliance_id]

    def get_corp_group(self, corp: EveCorporationInfo) -> Group:
        if corp.corporation_id not in self._corp_group_cache:
            self._corp_group_cache[corp.corporation_id] = self.create_corp_group(corp)
        return self._corp_group_cache[corp.corporation_id]

    def create_alliance_group(self, alliance: EveAllianceInfo) -> Group:
        with transaction.atomic():
            group, created = Group.objects.update_or_create(name=self.get_alliance_group_name(alliance))
            if created:
                ManagedAllianceGroup.objects.create(group=group, config=self, alliance=alliance)
            return group

    def create_corp_group(self, corp: EveCorporationInfo) -> Group:
        with transaction.atomic():
            group, created = Group.objects.update_or_create(name=self.get_corp_group_name(corp))
            if created:
                ManagedCorpGroup.objects.create(group=group, config=self, corp=corp)
            return group

    def delete_alliance_managed_groups(self):
        """
        Deletes ALL managed alliance groups
        """
        self.alliance_managed_groups.all().delete()

    def delete_corp_managed_groups(self):
        """
        Deletes ALL managed corp groups
        """
        self.corp_managed_groups.all().delete()

    def get_alliance_group_name(self, alliance: EveAllianceInfo) -> str:
        if self.alliance_name_source == self.OPT_TICKER:
            name = alliance.alliance_ticker
        elif self.alliance_name_source == self.OPT_NAME:
            name = alliance.alliance_name
        else:
            raise AttributeError('Not a valid name source')
        return self._replace_spaces(self.alliance_group_prefix + name)

    def get_corp_group_name(self, corp: EveCorporationInfo) -> str:
        if self.corp_name_source == self.OPT_TICKER:
            name = corp.corporation_ticker
        elif self.alliance_name_source == self.OPT_NAME:
            name = corp.corporation_name
        else:
            raise AttributeError('Not a valid name source')
        return self._replace_spaces(self.corp_group_prefix + name)

    def _replace_spaces(self, name: str) -> str:
        """
        Replace the spaces in the given name based on the config
        :param name: name to replace spaces in
        :return: name with spaces replaced with the configured character(s) or unchanged if configured
        """
        if self.replace_spaces:
            return name.replace(' ', str(self.replace_spaces_with))
        return name


class ManagedGroup(models.Model):
    group = models.ForeignKey(Group, on_delete=models.CASCADE)
    config = models.ForeignKey(AutogroupsConfig, on_delete=models.CASCADE)


class ManagedCorpGroup(ManagedGroup):
    corp = models.ForeignKey(EveCorporationInfo, on_delete=models.CASCADE)


class ManagedAllianceGroup(ManagedGroup):
    alliance = models.ForeignKey(EveAllianceInfo, on_delete=models.CASCADE)
