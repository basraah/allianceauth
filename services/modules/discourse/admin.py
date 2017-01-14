from __future__ import unicode_literals
from django.contrib import admin
from .models import DiscourseUser


class ProxyDiscourseUser(DiscourseUser):
    """
    Proxy model allows us to group all the services models together
    """
    class Meta:
        proxy = True
        app_label = 'services'
        verbose_name = DiscourseUser._meta.verbose_name
        verbose_name_plural = DiscourseUser._meta.verbose_name_plural


class DiscourseUserAdmin(admin.ModelAdmin):
        list_display = ('user',)
        search_fields = ('user__username',)

admin.site.register(ProxyDiscourseUser, DiscourseUserAdmin)
