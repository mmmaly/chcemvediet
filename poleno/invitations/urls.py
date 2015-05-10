# vim: expandtab
# -*- coding: utf-8 -*-
from django.conf.urls import patterns, url

from . import views

urlpatterns = patterns(u'',
    url(r'^accept/(?P<key>\w+)/$', views.accept, name=u'accept'),
)
