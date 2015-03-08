# vim: expandtab
# -*- coding: utf-8 -*-
from django.conf import settings as django_settings

def settings(request):
    return {
        u'DEBUG': django_settings.DEBUG,
        u'DEVBAR_MESSAGE': django_settings.DEVBAR_MESSAGE,
        }
