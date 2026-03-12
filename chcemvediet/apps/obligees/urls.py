# vim: expandtab
# -*- coding: utf-8 -*-
from django.urls import re_path

from . import views


app_name = u'obligees'

urlpatterns = [
    re_path(r'^$', views.index, name=u'index'),
    re_path(r'^autocomplete/$', views.autocomplete, name=u'autocomplete'),
]
