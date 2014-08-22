# vim: expandtab
from django.conf.urls import patterns, url

import views

urlpatterns = patterns(u'',
    url(r'^profile/$', views.profile, name=u'profile'),
)

