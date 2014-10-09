# vim: expandtab
# -*- coding: utf-8 -*-
from django.conf.urls import patterns, url

from . import views

urlpatterns = patterns(u'',
    url(r'^webhook/$', views.webhook, name=u'webhook'),
)
