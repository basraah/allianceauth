from __future__ import unicode_literals
from django.contrib import admin
from .models import OpenfireUser


class ProxyOpenfireUser(OpenfireUser):
    """
    Proxy model allows us to group all the services models together
    """
    class Meta:
        proxy = True
        app_label = 'services'
        verbose_name = OpenfireUser._meta.verbose_name
        verbose_name_plural = OpenfireUser._meta.verbose_name_plural


class OpenfireUserAdmin(admin.ModelAdmin):
        list_display = ('user', 'username')
        search_fields = ('user__username', 'username')

admin.site.register(ProxyOpenfireUser, OpenfireUserAdmin)
