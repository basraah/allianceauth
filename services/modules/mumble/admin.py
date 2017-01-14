from __future__ import unicode_literals
from django.contrib import admin
from .models import MumbleUser


class ProxyMumbleUser(MumbleUser):
    """
    Proxy model allows us to group all the services models together
    """
    class Meta:
        proxy = True
        app_label = 'services'
        verbose_name = MumbleUser._meta.verbose_name
        verbose_name_plural = MumbleUser._meta.verbose_name_plural


class MumbleUserAdmin(admin.ModelAdmin):
        fields = ('user', 'username', 'groups')  # pwhash is hidden from admin panel
        list_display = ('user', 'username', 'groups')
        search_fields = ('user__username', 'username', 'groups')

admin.site.register(ProxyMumbleUser, MumbleUserAdmin)
