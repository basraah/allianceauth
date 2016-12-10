class ServicesHook:
    """
    Abstract base class for creating a compatible services
    hook. Decorate with @register('services_hook') to have the
    services module registered for callbacks. Must be in
    auth_hook(.py) sub module
    """
    def __init__(self):
        self.urlpatterns = []

    def add_user(self, user):
        pass

    def delete_user(self, user):
        pass

    def update_groups(self, user):
        pass

    def update_password(self, user, password=None):
        pass

    def update_all_groups(self):
        """
        Iterate through and update all users groups
        """
        pass

    def disable_service(self):
        """
        Disables the entire service, deleting all user accounts
        """
        pass
