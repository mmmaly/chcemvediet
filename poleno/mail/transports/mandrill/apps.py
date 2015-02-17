# vim: expandtab
# -*- coding: utf-8 -*-
from django.apps import AppConfig

class MandrillConfig(AppConfig):
    name = u'poleno.mail.transports.mandrill'

    def ready(self):
        from . import signals
