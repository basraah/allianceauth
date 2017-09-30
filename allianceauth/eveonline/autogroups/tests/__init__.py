from unittest import mock

MODULE_PATH = 'allianceauth.eveonline.autogroups'


def patch(target, *args, **kwargs):
    return mock.patch('{}{}'.format(MODULE_PATH, target), *args, **kwargs)
