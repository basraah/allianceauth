import logging
from django.dispatch import receiver
from django.db.models.signals import pre_save, post_save, pre_delete
from allianceauth.authentication.models import UserProfile
from allianceauth.authentication.signals import state_changed
from allianceauth.eveonline.models import EveCharacter

from .models import AutogroupsConfig

logger = logging.getLogger(__name__)


@receiver(state_changed, sender=UserProfile)
def profile_state_changed(sender, user, state, **kwargs):
    """
    Receives a state change and triggers a group update for that user
    """
    logger.debug("Received state_changed from %s to state %s" % (user, state))
    AutogroupsConfig.objects.update_groups_for_user(user, state)


@receiver(pre_save, sender=AutogroupsConfig)
def pre_save_config(sender, instance, *args, **kwargs):
    """
    Checks if enable was toggled on group config and
    deletes groups if necessary.
    """
    logger.debug("Received pre_save from {}".format(instance))
    if not instance.pk:
        # new model being created
        return
    try:
        old_instance = AutogroupsConfig.objects.get(pk=instance.pk)

        # Check if enable was toggled, delete groups?
        if old_instance.alliance_groups is True and instance.alliance_groups is False:
            instance.delete_alliance_managed_groups()

        if old_instance.corp_groups is True and instance.corp_groups is False:
            instance.delete_corp_managed_groups()
    except AutogroupsConfig.DoesNotExist:
        pass


@receiver(pre_delete, sender=AutogroupsConfig)
def pre_delete_config(sender, instance, *args, **kwargs):
    """
    Delete groups on deleting config
    """
    instance.delete_corp_managed_groups()
    instance.delete_alliance_managed_groups()


@receiver(post_save, sender=EveCharacter)
def check_groups_on_character_update(sender, instance, *args, **kwargs):
    """
    Trigger check when main character model changes but state does not change.
    This signal will cause the group update to run twice if the
    users state changes as well. No easy way to suppress that
    """
    try:
        AutogroupsConfig.objects.update_groups_for_user(instance.userprofile.user)
    except UserProfile.DoesNotExist:
        # Not a main character
        pass


@receiver(pre_save, sender=UserProfile)
def check_groups_on_main_character_update(sender, instance, created, *args, **kwargs):
    """
    Trigger check when main character changes but state does not change.
    This signal will cause the group update to run twice if the
    users state changes as well. No easy way to suppress that
    """
    if not created:
        update_fields = kwargs.pop('update_fields', []) or []
        if 'main_character' in update_fields:
            AutogroupsConfig.objects.update_groups_for_user(instance.user)
