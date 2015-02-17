# vim: expandtab
# -*- coding: utf-8 -*-
from django.apps import AppConfig

class AttachmentsConfig(AppConfig):
    name = u'poleno.attachments'

    def ready(self):
        from . import signals
