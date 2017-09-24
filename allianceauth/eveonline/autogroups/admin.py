from django.contrib import admin
from .models import AutogroupsConfig


class AutogroupsConfigAdmin(admin.ModelAdmin):
    def get_readonly_fields(self, request, obj=None):
        if obj:  # This is the case when obj is already created i.e. it's an edit
            return [
                'corp_group_prefix', 'corp_name_source', 'alliance_group_prefix', 'alliance_name_source',
                'replace_spaces', 'replace_spaces_with'
            ]
        else:
            return []


admin.site.register(AutogroupsConfig, AutogroupsConfigAdmin)
