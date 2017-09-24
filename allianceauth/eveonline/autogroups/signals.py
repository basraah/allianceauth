import logging
from django.dispatch import receiver
from django.db.models.signals import pre_save, pre_delete
from allianceauth.authentication.models import State, UserProfile
from allianceauth.authentication.signals import state_changed

from .models import AutogroupsConfig

logger = logging.getLogger(__name__)


@receiver(state_changed, sender=UserProfile)
def profile_state_changed(sender, user, state, **kwargs):
    logger.debug("Received state_changed from %s to state %s" % (user, state))
    AutogroupsConfig.objects.update_groups_for_user(state, user)


@receiver(pre_save, sender=AutogroupsConfig)
def pre_save_user(sender, instance, *args, **kwargs):
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

# TODO Delete config signal

# TODO Signal: change main character but state doesnt change
# TODO Signal: change main character MODEL but state doesnt change
