# vim: expandtab
# -*- coding: utf-8 -*-
from django.apps import AppConfig

class InforequestsConfig(AppConfig):
    name = u'chcemvediet.apps.inforequests'

    def ready(self):
        from . import signals
