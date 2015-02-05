# vim: expandtab
# -*- coding: utf-8 -*-
from django.conf.urls import patterns, url
from django.utils.translation import ugettext_lazy as _

from . import views

urlpatterns = patterns(u'',
    url(_(r'^profile/$'), views.profile, name=u'profile'),
)

