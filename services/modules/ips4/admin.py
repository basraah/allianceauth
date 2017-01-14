from __future__ import unicode_literals
from django.contrib import admin
from .models import Ips4User


class ProxyIps4User(Ips4User):
    """
    Proxy model allows us to group all the services models together
    """
    class Meta:
        proxy = True
        app_label = 'services'
        verbose_name = Ips4User._meta.verbose_name
        verbose_name_plural = Ips4User._meta.verbose_name_plural


class Ips4UserAdmin(admin.ModelAdmin):
        list_display = ('user', 'username', 'id')
        search_fields = ('user__username', 'username', 'id')

admin.site.register(ProxyIps4User, Ips4UserAdmin)
