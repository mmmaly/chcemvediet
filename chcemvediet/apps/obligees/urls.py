# vim: expandtab
# -*- coding: utf-8 -*-
from django.conf.urls import url

from . import views


app_name = u'obligees'

urlpatterns = [
    url(r'^$', views.index, name=u'index'),
    url(r'^autocomplete/$', views.autocomplete, name=u'autocomplete'),
]
