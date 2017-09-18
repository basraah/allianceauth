from django.conf.urls import url

import allianceauth.timerboard.views

app_name = 'timerboard'

urlpatterns = [
    url(r'^$', allianceauth.timerboard.views.timer_view, name='view'),
    url(r'^add/$', allianceauth.timerboard.views.add_timer_view, name='add'),
    url(r'^remove/(\w+)$', allianceauth.timerboard.views.remove_timer, name='remove'),
    url(r'^edit/(\w+)$', allianceauth.timerboard.views.edit_timer, name='edit'),
    ]
