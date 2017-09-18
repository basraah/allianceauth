# -*- coding: utf-8 -*-
from setuptools import setup, find_packages
import allianceauth

EXCLUDE_FROM_PACKAGES = ['alliance_auth', 'thirdparty', 'test_allianceauth']

setup(
    name='allianceauth',
    version=allianceauth.__version__,
    author='Alliance Auth',
    author_email='adarnof@gmail.com',
    description='Eve alliance auth for the 99 percent',
    # Any changes in these package requirements
    # should be reflected in requirements.txt as well.
    install_requires=[
        'mysqlclient',
        'evelink',
        'dnspython',
        'passlib',
        'requests>=2.9.1',
        'bcrypt',
        'python-slugify>=1.2',
        'requests-oauthlib',

        'redis',
        'celery>=4.0.2',

        'django>=1.10,<2.0',
        'django-bootstrap-form',
        'django-bootstrap-pagination',
        'django-registration',
        'django-sortedm2m',
        'django-redis-cache>=1.7.1',
        'django-recaptcha',
        'django-celery-beat',
        'django-navhelper',

        # TODO split to openfire service
        # awating pyghassen/openfire-restapi #1 to fix installation issues
        'openfire-restapi',
        'sleekxmpp',

        'adarnauth-esi',
    ],
    dependency_links=[
        'https://github.com/adarnof/django-navhelper/tarball/master#egg=django-navhelper-0',
        'https://github.com/adarnof/openfire-restapi/tarball/master#egg=openfire-restapi-0',
        'https://github.com/adarnof/adarnauth-esi/tarball/master#egg=adarnauth-esi',
    ],
    license='GPLv2',
    packages=find_packages(exclude=EXCLUDE_FROM_PACKAGES),
    url='https://github.com/allianceauth/allianceauth',
    zip_safe=False,
    include_package_data=True,
)
