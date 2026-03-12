# vim: expandtab
# -*- coding: utf-8 -*-
from django.urls import re_path
from django.utils.translation import gettext_lazy as _

from poleno.utils.lazy import lazy_format

from . import views


app_name = u'accounts'

urlpatterns = [
    re_path(r'^profile/$', views.profile, name=u'profile'),
    re_path(lazy_format(r'^{0}/$',  _(u'accounts:urls:settings')), views.settings, name=u'settings'),
]
