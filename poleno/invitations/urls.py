# vim: expandtab
# -*- coding: utf-8 -*-
from django.urls import re_path

from . import views


app_name = u'invitations'

urlpatterns = [
    re_path(r'^$', views.invite, name=u'invite'),
    re_path(r'^accept/(?P<key>\w+)/$', views.accept, name=u'accept'),
]
