from django.contrib import admin
from .models import AutogroupsConfig

import logging


logger = logging.getLogger(__name__)


def sync_nickname(modeladmin, request, queryset):
    for agc in queryset:
        logger.debug("update_all_states_group_membership for {}".format(agc))
        agc.update_all_states_group_membership()


class AutogroupsConfigAdmin(admin.ModelAdmin):
    def get_readonly_fields(self, request, obj=None):
        if obj:  # This is the case when obj is already created i.e. it's an edit
            return [
                'corp_group_prefix', 'corp_name_source', 'alliance_group_prefix', 'alliance_name_source',
                'replace_spaces', 'replace_spaces_with'
            ]
        else:
            return []

    def get_actions(self, request):
        actions = super(AutogroupsConfigAdmin, self).get_actions(request)
        actions['sync_user_groups'] = (sync_nickname,
                                       'sync_user_groups',
                                       'Sync all users groups for this Autogroup Config')
        return actions


admin.site.register(AutogroupsConfig, AutogroupsConfigAdmin)
