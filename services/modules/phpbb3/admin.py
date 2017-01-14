from __future__ import unicode_literals
from django.contrib import admin
from .models import Phpbb3User


class ProxyPhpbb3User(Phpbb3User):
    """
    Proxy model allows us to group all the services models together
    """
    class Meta:
        proxy = True
        app_label = 'services'
        verbose_name = Phpbb3User._meta.verbose_name
        verbose_name_plural = Phpbb3User._meta.verbose_name_plural


class Phpbb3UserAdmin(admin.ModelAdmin):
        list_display = ('user', 'username')
        search_fields = ('user__username', 'username')

admin.site.register(ProxyPhpbb3User, Phpbb3UserAdmin)
