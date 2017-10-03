from django.views.generic.base import View
from django.http import HttpResponseRedirect


class NightModeRedirectView(View):
    SESSION_VAR = 'NIGHT_MODE'

    def get(self, request, *args, **kwargs):
        request.session[self.SESSION_VAR] = not request.session.get(self.SESSION_VAR, False)
        return HttpResponseRedirect(request.GET.get('next', '/'))
