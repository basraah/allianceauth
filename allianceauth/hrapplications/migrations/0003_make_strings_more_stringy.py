# -*- coding: utf-8 -*-
# Generated by Django 1.10.5 on 2017-03-22 23:35
from __future__ import unicode_literals

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('hrapplications', '0002_choices_for_questions'),
    ]

    operations = [
        migrations.AlterField(
            model_name='hrapplication',
            name='about',
            field=models.TextField(default=''),
        ),
        migrations.AlterField(
            model_name='hrapplication',
            name='character_name',
            field=models.CharField(default='', max_length=254),
        ),
        migrations.AlterField(
            model_name='hrapplication',
            name='extra',
            field=models.TextField(default=''),
        ),
        migrations.AlterField(
            model_name='hrapplication',
            name='full_api_id',
            field=models.CharField(default='', max_length=254),
        ),
        migrations.AlterField(
            model_name='hrapplication',
            name='full_api_key',
            field=models.CharField(default='', max_length=254),
        ),
        migrations.AlterField(
            model_name='hrapplication',
            name='is_a_spi',
            field=models.CharField(default='', max_length=254),
        ),
        migrations.AlterField(
            model_name='hrapplicationcomment',
            name='comment',
            field=models.CharField(default='', max_length=254),
        ),
    ]
