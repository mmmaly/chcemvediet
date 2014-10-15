# vim: expandtab
# -*- coding: utf-8 -*-
from django.conf.urls import patterns, url

from poleno.utils.tests.test_templatetags import views

urlpatterns = patterns(u'',
    url(r'^$', views.active_view, name=u'index'),
    url(r'^first/', views.active_view, name=u'first'),
)
