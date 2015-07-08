# vim: expandtab
# -*- coding: utf-8 -*-
from django.conf.urls import patterns, url

from . import views

urlparams = dict(
        lang=r'(?P<lang>\w+)',
        path=r'(?P<path>(?:|[a-z0-9/-]*/))',
        name=r'(?P<name>[a-z0-9-]+[.][a-z0-9-.]+)',
        )

urlpatterns = patterns(u'',
    url(r'^alternatives/{lang}/{path}$'.format(**urlparams), views.alternatives, name=u'alternatives'),
    url(r'^{path}$'.format(**urlparams), views.view, name=u'view'),
    url(r'^{path}{name}$'.format(**urlparams), views.file, name=u'file'),
)
