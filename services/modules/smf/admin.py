from __future__ import unicode_literals
from django.contrib import admin
from .models import SmfUser


class ProxySmfUser(SmfUser):
    """
    Proxy model allows us to group all the services models together
    """
    class Meta:
        proxy = True
        app_label = 'services'
        verbose_name = SmfUser._meta.verbose_name
        verbose_name_plural = SmfUser._meta.verbose_name_plural


class SmfUserAdmin(admin.ModelAdmin):
        list_display = ('user', 'username')
        search_fields = ('user__username', 'username')

admin.site.register(ProxySmfUser, SmfUserAdmin)
