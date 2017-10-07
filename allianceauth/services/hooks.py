from django.conf.urls import include, url
from django.template.loader import render_to_string
from django.conf import settings

from allianceauth.hooks import get_hooks


class ServicesHook:
    """
    Abstract base class for creating a compatible services
    hook. Decorate with @register('services_hook') to have the
    services module registered for callbacks. Must be in
    auth_hook(.py) sub module
    """
    def __init__(self):
        self.name = 'Undefined'
        self.urlpatterns = []
        self.service_ctrl_template = 'services/services_ctrl.html'
        self.access_perm = None

    @property
    def title(self):
        """
        A nicely formatted title of the service, for client facing
        display.
        :return: str
        """
        return self.name.title()

    def delete_user(self, user, notify_user=False):
        """
        Delete the users service account, optionally notify them
        that the service has been disabled
        :param user: Django.contrib.auth.models.User
        :param notify_user: Whether the service should sent a
        notification to the user about the disabling of their
        service account.
        :return: True if the service account has been disabled,
        or False if it doesnt exist.
        """
        pass

    def validate_user(self, user):
        pass

    def sync_nickname(self, user):
        """
        Sync the users nickname
        :param user: Django.contrib.auth.models.User
        :return: None
        """
        pass

    def update_groups(self, user):
        """
        Update the users group membership
        :param user: Django.contrib.auth.models.User
        :return: None
        """
        pass

    def update_all_groups(self):
        """
        Iterate through and update all users groups
        :return: None
        """
        pass

    def service_active_for_user(self, user):
        pass

    def show_service_ctrl(self, user):
        """
        Whether the service control should be displayed to the given user
        who has the given service state. Usually this function wont
        require overloading.
        :param user: django.contrib.auth.models.User
        :return: bool True if the service should be shown
        """
        return self.service_active_for_user(user) or user.is_superuser

    def render_services_ctrl(self, request):
        """
        Render the services control template row
        :param request:
        :return:
        """
        return ''

    def __str__(self):
        return self.name or 'Unknown Service Module'

    class Urls:
        def __init__(self):
            self.auth_activate = ''
            self.auth_set_password = ''
            self.auth_reset_password = ''
            self.auth_deactivate = ''

    @staticmethod
    def get_services():
        for fn in get_hooks('services_hook'):
            yield fn()


class MenuItemHook:
    def __init__(self, text, classes, url_name, order=None, navactive=list([])):
        self.text = text
        self.classes = classes
        self.url_name = url_name
        self.template = 'public/menuitem.html'
        self.order = order if order is not None else 9999
        navactive = navactive or []
        navactive.append(url_name)
        self.navactive = navactive

    def render(self, request):
        return render_to_string(self.template,
                                {'item': self},
                                request=request)


class UrlHook:
    def __init__(self, urls, namespace, base_url):
        self.include_pattern = url(base_url, include(urls, namespace=namespace))

class NameFormatter:

    DEFAULT_FORMAT = getattr(settings, "DEFAULT_SERVICE_NAME_FORMAT", '[{corp_ticker}] {character_name}')

    def __init__(self, service):
        """
        :param service: ServicesHook of the service to generate the name for.
        """
        self.service = service

        try:
            self.format_config = NameFormatConfig.objects.get(service_name=self.service.name)
        except NameFormatConfig.DoesNotExist:
            self.format_config = None

    def format_name(self, user):
        """
        :param user: django.contrib.auth.models.User to generate name for
        :return: str Generated name
        """

        # Get data
        main_char = EveManager.get_main_character(user)
        formatter = self._get_formatter(main_char)

        format_data = {
            'character_name': getattr(main_char, 'character_name',
                                      user.username if self._default_to_username() else None),
            'character_id': getattr(main_char, 'character_id', None),
            'corp_ticker': getattr(main_char, 'corporation_ticker', None),
            'corp_name': getattr(main_char, 'corporation_name', None),
            'corp_id': getattr(main_char, 'corporation_id', None),
            'alliance_name': getattr(main_char, 'alliance_name', None),
            'alliance_ticker': None,
            'alliance_id': getattr(main_char, 'alliance_id', None),
            'username': user.username,
        }

        if main_char is not None and 'alliance_ticker' in formatter:
            format_data['alliance_ticker'] = EveManager.get_alliance(main_char.alliance_id).ticker

        return formatter.format(**format_data)

    def _get_formatter(self, character):
        """
        Try to get the config format first
        Then the service default
        Before finally defaulting to global default
        :param character: EveCharacter
        :return: str
        """
        fallback_format = self._get_default_formatter()
        if character is not None and character.in_organisation():
            # Has a character, and is in organisation
            return getattr(self.format_config, 'format', fallback_format)
        else:
            # No character or not in organisation
            # Try to use nontenant format first, otherwise use the format and then other defaults
            return getattr(self.format_config, 'nontenant_format',
                           getattr(self.format_config, 'format', fallback_format))

    def _get_default_formatter(self):
        return getattr(self.service, 'name_format', self.DEFAULT_FORMAT)

    def _default_to_username(self):
        """
        Default to a users username if they have no main character.
        Default is True
        :return: bool
        """
        return getattr(self.format_config, 'default_to_username', True)
