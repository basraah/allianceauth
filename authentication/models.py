from __future__ import unicode_literals
from django.utils.encoding import python_2_unicode_compatible
from django.db import models
from django.contrib.auth.models import User
from authentication.states import MEMBER_STATE, BLUE_STATE, NONE_STATE
from eveonline.models import EveCharacter


@python_2_unicode_compatible
class AuthServicesInfo(models.Model):
    class Meta:
        default_permissions = ('change',)

    STATE_CHOICES = (
        (NONE_STATE, 'None'),
        (BLUE_STATE, 'Blue'),
        (MEMBER_STATE, 'Member'),
    )

    main_character = models.ForeignKey(EveCharacter, on_delete=models.SET_NULL, blank=True, null=True, default=None)
    user = models.OneToOneField(User)
    state = models.CharField(blank=True, null=True, choices=STATE_CHOICES, default=NONE_STATE, max_length=10)

    # Faux main_char_id properties for backwards compatibility
    @property
    def main_char_id(self):
        return self.main_character.character_id

    @main_char_id.setter
    def main_char_id(self, char_id):
        self.main_character = EveCharacter.objects.get(character_id=char_id)

    def __str__(self):
        return self.user.username + ' - AuthInfo'
