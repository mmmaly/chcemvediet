# vim: expandtab
# -*- coding: utf-8 -*-
from django.conf.urls import patterns, url

import .views

urlpatterns = patterns(u'',
    url(r'^profile/$', views.profile, name=u'profile'),
)

