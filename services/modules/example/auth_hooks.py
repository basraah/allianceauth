from __future__ import unicode_literals
from services.hooks import ServicesHook
from alliance_auth import hooks

from .urls import urlpatterns


class ExampleService(ServicesHook):
    def __init__(self):
        ServicesHook.__init__(self)
        self.urlpatterns = urlpatterns

    """
    Overload base methods here to implement functionality
    """


@hooks.register('services_hook')
def register_service():
    return ExampleService()
