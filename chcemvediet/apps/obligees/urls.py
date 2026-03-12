# vim: expandtab
# -*- coding: utf-8 -*-
from django.conf.urls import url

from . import views


urlpatterns = [
    url(r'^$', views.index, name=u'index'),
    url(r'^autocomplete/$', views.autocomplete, name=u'autocomplete'),
]
