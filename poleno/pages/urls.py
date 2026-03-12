# vim: expandtab
# -*- coding: utf-8 -*-
from django.urls import re_path

from . import views


urlparams = dict(
        lang=r'(?P<lang>\w+)',
        path=r'(?P<path>(?:|[a-z0-9/-]*/))',
        name=r'(?P<name>[a-z0-9-]+[.][a-z0-9-.]+)',
        )

app_name = u'pages'

urlpatterns = [
    re_path(r'^alternatives/{lang}/{path}$'.format(**urlparams), views.alternatives, name=u'alternatives'),
    re_path(r'^{path}$'.format(**urlparams), views.view, name=u'view'),
    re_path(r'^{path}{name}$'.format(**urlparams), views.file, name=u'file'),
]
