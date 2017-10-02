import logging
from django.db import models, transaction
from django.contrib.auth.models import Group, User
from django.core.exceptions import ObjectDoesNotExist

from allianceauth.authentication.models import State
from allianceauth.eveonline.models import EveCorporationInfo, EveAllianceInfo

logger = logging.getLogger(__name__)


def get_users_for_state(state: State):
    return User.objects.select_related('profile').prefetch_related('profile__main_character')\
            .filter(profile__state__pk=state.pk)


class AutogroupsConfigManager(models.Manager):
    def update_groups_for_state(self, state: State):
        """
        Update all the Group memberships for the users
        who have State
        :param state: State to update for
        :return:
        """
        users = get_users_for_state(state)
        for config in self.filter(states=state):
            logger.debug("in state loop")
            for user in users:
                logger.debug("in user loop for {}".format(user))
                config.update_group_membership_for_user(user)

    def update_groups_for_user(self, user: User, state: State = None):
        """
        Update the Group memberships for the given users state
        :param user: User to update for
        :param state: State to update user for
        :return:
        """
        if state is None:
            state = user.profile.state
        for config in self.filter(states=state):
                config.update_group_membership_for_user(user)


class AutogroupsConfig(models.Model):
    OPT_TICKER = 'ticker'
    OPT_NAME = 'name'
    NAME_OPTIONS = (
        (OPT_TICKER, 'Ticker'),
        (OPT_NAME, 'Full name'),
    )

    states = models.ManyToManyField(State, related_name='autogroups')

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

    def __repr__(self):
        return self.__class__.__name__

    def __str__(self):
        return 'States: ' + (' '.join(list(self.states.all().values_list('name', flat=True))) if self.pk else str(None))

    def update_all_states_group_membership(self):
        list(map(self.update_group_membership_for_state, self.states.all()))

    def update_group_membership_for_state(self, state: State):
        list(map(self.update_group_membership_for_user, get_users_for_state(state)))

    @transaction.atomic
    def update_group_membership_for_user(self, user: User):
        self.update_alliance_group_membership(user)
        self.update_corp_group_membership(user)

    def user_entitled_to_groups(self, user: User) -> bool:
        try:
            return user.profile.state in self.states.all()
        except ObjectDoesNotExist:
            return False

    @transaction.atomic
    def update_alliance_group_membership(self, user: User):
        self.remove_user_from_alliance_groups(user)  # TODO more efficient way of doing this
        if not self.alliance_groups or not self.user_entitled_to_groups(user):
            return
        try:
            alliance = user.profile.main_character.alliance
            if alliance is None:
                return
            group = self.get_alliance_group(user.profile.main_character.alliance)
            user.groups.add(group)
        except EveAllianceInfo.DoesNotExist:
            logger.warning('User {} main characters alliance does not exist in the database.'
                           ' Group membership not updated'.format(user))
        except AttributeError:
            logger.warning('User {} does not have a main character. Group membership not updated'.format(user))

    @transaction.atomic
    def update_corp_group_membership(self, user: User):
        self.remove_user_from_corp_groups(user)  # TODO more efficient way of doing this
        if not self.corp_groups or not self.user_entitled_to_groups(user):
            return
        try:
            corp = user.profile.main_character.corporation
            group = self.get_corp_group(corp)

            user.groups.add(group)
        except EveCorporationInfo.DoesNotExist:
            logger.warning('User {} main characters corporation does not exist in the database.'
                           ' Group membership not updated'.format(user))
        except AttributeError:
            logger.warning('User {} does not have a main character. Group membership not updated'.format(user))

    @transaction.atomic
    def remove_user_from_alliance_groups(self, user: User):
        # TODO: find a better way
        remove_groups = user.groups.filter(pk__in=self.alliance_managed_groups.all().values_list('pk', flat=True))
        list(map(user.groups.remove, remove_groups))

    @transaction.atomic
    def remove_user_from_corp_groups(self, user: User):
        remove_groups = user.groups.filter(pk__in=self.corp_managed_groups.all().values_list('pk', flat=True))
        list(map(user.groups.remove, remove_groups))

    def get_alliance_group(self, alliance: EveAllianceInfo) -> Group:
        return self.create_alliance_group(alliance)

    def get_corp_group(self, corp: EveCorporationInfo) -> Group:
        return self.create_corp_group(corp)

    @transaction.atomic
    def create_alliance_group(self, alliance: EveAllianceInfo) -> Group:
        group, created = Group.objects.get_or_create(name=self.get_alliance_group_name(alliance))
        if created:
            ManagedAllianceGroup.objects.create(group=group, config=self, alliance=alliance)
        return group

    @transaction.atomic
    def create_corp_group(self, corp: EveCorporationInfo) -> Group:
        group, created = Group.objects.get_or_create(name=self.get_corp_group_name(corp))
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
            return name.strip().replace(' ', str(self.replace_spaces_with))
        return name


class ManagedGroup(models.Model):
    group = models.ForeignKey(Group, on_delete=models.CASCADE)
    config = models.ForeignKey(AutogroupsConfig, on_delete=models.CASCADE)


class ManagedCorpGroup(ManagedGroup):
    corp = models.ForeignKey(EveCorporationInfo, on_delete=models.CASCADE)


class ManagedAllianceGroup(ManagedGroup):
    alliance = models.ForeignKey(EveAllianceInfo, on_delete=models.CASCADE)
