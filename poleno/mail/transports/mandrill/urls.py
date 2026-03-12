# vim: expandtab
# -*- coding: utf-8 -*-
from django.urls import re_path

from . import views


app_name = u'mandrill'

urlpatterns = [
    re_path(r'^webhook/$', views.webhook, name=u'webhook'),
]
