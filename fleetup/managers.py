from __future__ import unicode_literals
from django.conf import settings
from django.core.cache import cache
from datetime import datetime

import logging
import requests
import hashlib

logger = logging.getLogger(__name__)


class FleetUpManager:
    APP_KEY = settings.FLEETUP_APP_KEY
    USER_ID = settings.FLEETUP_USER_ID
    API_ID = settings.FLEETUP_API_ID
    GROUP_ID = settings.FLEETUP_GROUP_ID
    BASE_URL = "http://api.fleet-up.com/Api.svc/{}/{}/{}".format(APP_KEY, USER_ID, API_ID)

    def __init__(self):
        pass

    @classmethod
    def _request_cache_key(cls, url):
        h = hashlib.sha1()
        h.update(url)
        return 'FLEETUP_ENDPOINT_' + h.hexdigest()

    @classmethod
    def _cache_until_seconds(cls, cache_until_json):
        # Format comes in like "/Date(1493896236163)/"
        try:
            epoch_ms = int(cache_until_json[6:-2])
            cache_delta = datetime.fromtimestamp(epoch_ms/1000) - datetime.now()
            cache_delta_seconds = cache_delta.total_seconds()
            if cache_delta_seconds < 0:
                return 0
            elif cache_delta_seconds > 3600:
                return 3600
            else:
                return cache_delta_seconds
        except TypeError:
            logger.debug("Couldn't convert CachedUntil time, defaulting to 600 seconds")
        return 600

    @classmethod
    def get_endpoint(cls, url):
        try:
            cache_key = cls._request_cache_key(url)
            cached = cache.get(cache_key)
            if cached:
                return cached

            r = requests.get(url)
            r.raise_for_status()

            json = r.json()

            if json['Success']:
                cache.set(cache_key, json, cls._cache_until_seconds(json['CachedUntilUTC']))
            return json
        except requests.exceptions.ConnectionError:
            logger.warn("Can't connect to Fleet-Up API, is it offline?!")
        except requests.HTTPError:
            logger.exception("Error accessing Fleetup API")
        return None

    @classmethod
    def get_fleetup_members(cls):
        url = "{}/GroupCharacters/{}".format(cls.BASE_URL, cls.GROUP_ID)
        try:
            fmembers = cls.get_endpoint(url)
            if not fmembers:
                return None
            return {row["UserId"]: {"user_id": row["UserId"],
                                    "char_name": row["EveCharName"],
                                    "char_id": row["EveCharId"],
                                    "corporation": row["Corporation"]} for row in fmembers["Data"]}
        except (ValueError, UnicodeDecodeError, TypeError):
            logger.debug("No fleetup members retrieved.")
        return {}

    @classmethod
    def get_fleetup_operations(cls):
        url = "{}/Operations/{}".format(cls.BASE_URL, cls.GROUP_ID)
        try:
            foperations = cls.get_endpoint(url)
            if foperations is None:
                return None
            return {row["StartString"]: {"subject": row["Subject"],
                                         "start": (datetime.strptime(row["StartString"], "%Y-%m-%d %H:%M:%S")),
                                         "end": (datetime.strptime(row["EndString"], "%Y-%m-%d %H:%M:%S")),
                                         "operation_id": row["OperationId"],
                                         "location": row["Location"],
                                         "location_info": row["LocationInfo"],
                                         "details": row["Details"],
                                         "url": row["Url"],
                                         "doctrine": row["Doctrines"],
                                         "organizer": row["Organizer"]} for row in foperations["Data"]}
        except (ValueError, UnicodeDecodeError):
            logger.debug("No fleetup operations retrieved.")
        return {}

    @classmethod
    def get_fleetup_timers(cls):
        url = "{}/Timers/{}".format(cls.BASE_URL, cls.GROUP_ID)
        try:
            ftimers = cls.get_endpoint(url)
            if not ftimers:
                return None
            return {row["ExpiresString"]: {"solarsystem": row["SolarSystem"],
                                           "planet": row["Planet"],
                                           "moon": row["Moon"],
                                           "owner": row["Owner"],
                                           "type": row["Type"],
                                           "timer_type": row["TimerType"],
                                           "expires": (datetime.strptime(row["ExpiresString"], "%Y-%m-%d %H:%M:%S")),
                                           "notes": row["Notes"]} for row in ftimers["Data"]}
        except requests.exceptions.ConnectionError:
            logger.warn("Can't connect to Fleet-Up API, is it offline?!")
        except (ValueError, UnicodeDecodeError, TypeError):
            logger.debug("No fleetup timers retrieved.")
        return {}

    @classmethod
    def get_fleetup_doctrines(cls):
        url = "{}/Doctrines/{}".format(cls.BASE_URL, cls.GROUP_ID)
        try:
            fdoctrines = cls.get_endpoint(url)
            if not fdoctrines:
                return None
            return {"fleetup_doctrines": fdoctrines["Data"]}
        except (ValueError, UnicodeDecodeError):
            logger.debug("No fleetup doctrines retrieved.")
        return {"fleetup_doctrines": []}

    @classmethod
    def get_fleetup_doctrine(cls, doctrinenumber):
        url = "{}/DoctrineFittings/{}".format(cls.BASE_URL, doctrinenumber)
        try:
            fdoctrine = cls.get_endpoint(url)
            if not fdoctrine:
                return None
            return {"fitting_doctrine": fdoctrine}
        except requests.exceptions.ConnectionError:
            logger.warn("Can't connect to Fleet-Up API, is it offline?!")
        except (ValueError, UnicodeDecodeError):
            logger.warn("Fleetup doctrine number %s not found" % doctrinenumber)
        return {"fitting_doctrine": {}}

    @classmethod
    def get_fleetup_fittings(cls):
        url = "{}/Fittings/{}".format(cls.BASE_URL, cls.GROUP_ID)
        try:
            ffittings = cls.get_endpoint(url)
            if not ffittings:
                return None
            return {row["FittingId"]: {"fitting_id": row["FittingId"],
                                       "name": row["Name"],
                                       "icon_id": row["EveTypeId"],
                                       "hull": row["HullType"],
                                       "shiptype": row["ShipType"],
                                       "estimated": row["EstPrice"],
                                       "faction": row["Faction"],
                                       "categories": row["Categories"],
                                       "last_update": (
                                       datetime.strptime(row["LastUpdatedString"], "%Y-%m-%d %H:%M:%S"))} for row in
                    ffittings["Data"]}
        except (ValueError, UnicodeDecodeError, TypeError):
            logger.debug("No fleetup fittings retrieved.")
        return {}

    @classmethod
    def get_fleetup_fitting(cls, fittingnumber):
        url = "{}/Fitting/{}".format(cls.BASE_URL, fittingnumber)
        try:
            ffitting = cls.get_endpoint(url)
            if not ffitting:
                return None
            return {"fitting_data": ffitting["Data"]}
        except (ValueError, UnicodeDecodeError):
            logger.warn("Fleetup fitting number %s not found" % fittingnumber)
        except KeyError:
            logger.warn("Failed to retrieve fleetup fitting number %s" % fittingnumber)
        return {"fitting_data": {}}

    @classmethod
    def get_fleetup_doctrineid(cls, fittingnumber):
        url = "{}/Fitting/{}".format(cls.BASE_URL, fittingnumber)
        try:
            fdoctrineid = cls.get_endpoint(url)
            if not fdoctrineid:
                return None
            return fdoctrineid['Data']['Doctrines'][0]['DoctrineId']
        except (ValueError, UnicodeDecodeError):
            logger.warn("Fleetup doctrine number not found for fitting number %s" % fittingnumber)
        except (KeyError, IndexError):
            logger.debug("Fleetup fitting number %s not in a doctrine." % fittingnumber)
        return {}

    @classmethod
    def get_fleetup_fitting_eft(cls, fittingnumber):
        url = "{}/Fitting/{}/eft".format(cls.BASE_URL, fittingnumber)
        try:
            ffittingeft = cls.get_endpoint(url)
            if not ffittingeft:
                return None
            return {"fitting_eft": ffittingeft["Data"]["FittingData"]}
        except (ValueError, UnicodeDecodeError):
            logger.warn("Fleetup fitting eft not found for fitting number %s" % fittingnumber)
        return {"fitting_eft": {}}
