# vim: expandtab
# -*- coding: utf-8 -*-
from django.conf.urls import url

from . import views


app_name = u'mandrill'

urlpatterns = [
    url(r'^webhook/$', views.webhook, name=u'webhook'),
]
