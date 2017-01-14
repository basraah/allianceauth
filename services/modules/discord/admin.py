from __future__ import unicode_literals
from django.contrib import admin
from .models import DiscordUser


class ProxyDiscordUser(DiscordUser):
    """
    Proxy model allows us to group all the services models together
    """
    class Meta:
        proxy = True
        app_label = 'services'
        verbose_name = DiscordUser._meta.verbose_name
        verbose_name_plural = DiscordUser._meta.verbose_name_plural


class DiscordUserAdmin(admin.ModelAdmin):
        list_display = ('user', 'uid')
        search_fields = ('user__username', 'uid')

admin.site.register(ProxyDiscordUser, DiscordUserAdmin)
