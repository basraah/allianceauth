from django.db import models
from django.contrib import admin
from django import forms
from allianceauth import hooks
from allianceauth.authentication.models import State


class NameFormatConfig(models.Model):
    service_name = models.CharField(max_length=100, blank=False, null=False)
    default_to_username = models.BooleanField(default=True, help_text="If a user has no main_character, "
                                                                      "default to using their Auth username instead.")
    format = models.CharField(max_length=100, blank=False, null=False,
                              help_text='For information on constructing name formats, please see the '
                                        '<a href="https://allianceauth.readthedocs.io/en/latest/features/nameformats">'
                                        'name format documentation</a>')
    states = models.ManyToManyField(State, help_text="States to apply this format to. You should only have one "
                                                     "formatter for each state for each service.")


class NameFormatConfigForm(forms.ModelForm):
    def __init__(self, *args, **kwargs):
        super(NameFormatConfigForm, self).__init__(*args, **kwargs)
        SERVICE_CHOICES = [(s.name, s.name) for h in hooks.get_hooks('services_hook') for s in [h()]]
        if self.instance.id:
            SERVICE_CHOICES.append((self.instance.field, self.instance.field))
        self.fields['service_name'] = forms.ChoiceField(choices=SERVICE_CHOICES)


class NameFormatConfigAdmin(admin.ModelAdmin):
    form = NameFormatConfigForm


admin.site.register(NameFormatConfig, NameFormatConfigAdmin)
