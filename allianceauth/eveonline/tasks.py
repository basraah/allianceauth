import logging

from allianceauth.celery import app
from .models import EveAllianceInfo
from .models import EveCharacter
from .models import EveCorporationInfo

logger = logging.getLogger(__name__)


@app.task
def update_corp(corp_id):
    EveCorporationInfo.objects.update_corporation(corp_id)


@app.task
def update_alliance(alliance_id):
    EveAllianceInfo.objects.update_alliance(alliance_id).populate_alliance()


@app.task
def update_character(character_id):
    EveCharacter.objects.update_character(character_id)


@app.task
def run_model_update():
    # update existing corp models
    for corp in EveCorporationInfo.objects.all().values('corporation_id'):
        update_corp.delay(corp['corporation_id'])

    # update existing alliance models
    for alliance in EveAllianceInfo.objects.all().values('alliance_id'):
        update_alliance.delay(alliance['alliance_id'])

    for character in EveCharacter.objects.all().values('character_id'):
        update_character.delay(character['character_id'])
