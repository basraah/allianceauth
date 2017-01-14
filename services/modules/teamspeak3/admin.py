from __future__ import unicode_literals
from django.contrib import admin
from .models import AuthTS, Teamspeak3User


class ProxyTeamspeak3User(Teamspeak3User):
    """
    Proxy model allows us to group all the services models together
    """
    class Meta:
        proxy = True
        app_label = 'services'
        verbose_name = Teamspeak3User._meta.verbose_name
        verbose_name_plural = Teamspeak3User._meta.verbose_name_plural


class Teamspeak3UserAdmin(admin.ModelAdmin):
        list_display = ('user', 'uid', 'perm_key')
        search_fields = ('user__username', 'uid', 'perm_key')


class AuthTSgroupAdmin(admin.ModelAdmin):
    fields = ['auth_group', 'ts_group']
    filter_horizontal = ('ts_group',)


admin.site.register(AuthTS, AuthTSgroupAdmin)
admin.site.register(ProxyTeamspeak3User, Teamspeak3UserAdmin)
