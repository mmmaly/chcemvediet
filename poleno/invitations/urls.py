# vim: expandtab
# -*- coding: utf-8 -*-
from django.conf.urls import url

from . import views


app_name = u'invitations'

urlpatterns = [
    url(r'^$', views.invite, name=u'invite'),
    url(r'^accept/(?P<key>\w+)/$', views.accept, name=u'accept'),
]
