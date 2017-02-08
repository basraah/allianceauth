# -*- coding: utf-8 -*-
# Generated by Django 1.10.5 on 2017-02-02 05:59
from __future__ import unicode_literals

from django.db import migrations
from django.conf import settings
from django.core.exceptions import ObjectDoesNotExist
from django.contrib.auth.management import create_permissions

import logging

logger = logging.getLogger(__name__)


def migrate_service_enabled(apps, schema_editor):
    for app_config in apps.get_app_configs():
        app_config.models_module = True
        create_permissions(app_config, apps=apps, verbosity=0)
        app_config.models_module = None

    Group = apps.get_model("auth", "Group")
    Permission = apps.get_model("auth", "Permission")
    IpboardUser = apps.get_model("ipboard", "IpboardUser")

    perm = Permission.objects.get(codename='access_ipboard')

    member_group_name = getattr(settings, str('DEFAULT_AUTH_GROUP'), 'Member')
    blue_group_name = getattr(settings, str('DEFAULT_BLUE_GROUP'), 'Blue')

    # Migrate members
    if IpboardUser.objects.filter(user__groups__name=member_group_name).exists() or \
            getattr(settings, str('ENABLE_AUTH_IPBOARD'), False):
        try:
            group = Group.objects.get(name=member_group_name)
            group.permissions.add(perm)
        except ObjectDoesNotExist:
            logger.warning('Failed to migrate ENABLE_AUTH_IPBOARD setting')

    # Migrate blues
    if IpboardUser.objects.filter(user__groups__name=blue_group_name).exists() or \
            getattr(settings, str('ENABLE_BLUE_IPBOARD'), False):
        try:
            group = Group.objects.get(name=blue_group_name)
            group.permissions.add(perm)
        except ObjectDoesNotExist:
            logger.warning('Failed to migrate ENABLE_BLUE_IPBOARD setting')


class Migration(migrations.Migration):

    dependencies = [
        ('ipboard', '0001_initial'),
    ]

    operations = [
        migrations.AlterModelOptions(
            name='ipboarduser',
            options={'permissions': (('access_ipboard', 'Can access the IPBoard service'),)},
        ),
        migrations.RunPython(migrate_service_enabled),
    ]
