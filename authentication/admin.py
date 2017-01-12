from __future__ import unicode_literals

from django.contrib import admin
from django.contrib.auth.admin import UserAdmin as BaseUserAdmin
from django.contrib.auth.models import User
from django.utils.text import slugify

from authentication.models import AuthServicesInfo
from eveonline.models import EveCharacter
from alliance_auth.hooks import get_hooks
from services.hooks import ServicesHook


@admin.register(AuthServicesInfo)
class AuthServicesInfoManager(admin.ModelAdmin):

    @staticmethod
    def main_character(obj):
        if obj.main_char_id:
            try:
                return EveCharacter.objects.get(character_id=obj.main_char_id)
            except EveCharacter.DoesNotExist:
                pass
        return None

    # TODO: This would be good to convert into a ServiceHook call
    """
    def sync_nicknames(self, request, queryset):
        count = 0
        for a in queryset:
            if a.discord_uid != "":
                update_discord_nickname(a.user.pk)
                count += 1
        self.message_user(request, "%s discord accounts queued for nickname sync." % count)

    sync_nicknames.short_description = "Sync nicknames for selected discord accounts"
    """

    search_fields = [
        'user__username',
        'main_char_id',
    ]
    list_display = ('user', 'main_character')


def make_service_hooks_update_groups_action(service):
    """
    Make a admin action for the given service
    :param service: services.hooks.ServicesHook
    :return: fn to update services groups for the selected users
    """
    def update_service_groups(modeladmin, request, queryset):
        for user in queryset:  # queryset filtering doesn't work here?
            service.update_groups(user)

    update_service_groups.__name__ = str('update_{}_groups'.format(slugify(service.name)))
    update_service_groups.short_description = "Sync {} groups for selected users".format(service.title)
    return update_service_groups


class UserAdmin(BaseUserAdmin):
    """
    Extending Django's UserAdmin model
    """
    def get_actions(self, request):
        actions = super(BaseUserAdmin, self).get_actions(request)

        for hook in get_hooks('services_hook'):
            svc = hook()
            # Check update_groups is redefined/overloaded
            if svc.update_groups.__module__ != ServicesHook.update_groups.__module__:
                action = make_service_hooks_update_groups_action(svc)
                actions[action.__name__] = (action,
                                            action.__name__,
                                            action.short_description)

        return actions

# Re-register UserAdmin
try:
    admin.site.unregister(User)
finally:
    admin.site.register(User, UserAdmin)
