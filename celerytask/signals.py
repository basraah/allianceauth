from django.db.models.signals import m2m_changed
from django.dispatch import receiver
from django.contrib.auth.models import User
import logging
from .tasks import update_jabber_groups
from .tasks import update_mumble_groups
from .tasks import update_forum_groups
from .tasks import update_ipboard_groups
from .tasks import update_discord_groups
from .tasks import update_teamspeak3_groups
from authentication.models import AuthServicesInfo

logger = logging.getLogger(__name__)

@receiver(m2m_changed, sender=User.groups.through)
def m2m_changed_user_groups(sender, instance, action, *args, **kwargs):
    logger.debug("Received m2m_changed from %s groups with action %s" % (instance, action))
    if action=="post_add" or action=="post_remove" or action=="post_clear":
        logger.debug("Triggering service group update for %s" % instance)
        auth, c = AuthServicesInfo.objects.get_or_create(user=instance)
        if auth.jabber_username:
            update_jabber_groups.delay(instance.pk)
        if auth.teamspeak3_uid:
            update_teamspeak3_groups.delay(instance.pk)
        if auth.forum_username:
            update_forum_groups.delay(instance.pk)
        if auth.ipboard_username:
            update_ipboard_groups.delay(instance.pk)
        if auth.discord_uid:
            update_discord_groups.delay(instance.pk)
        if auth.mumble_username:
            update_mumble_groups.delay(instance.pk)