# vim: expandtab
# -*- coding: utf-8 -*-
from django.apps import AppConfig

class PagesConfig(AppConfig):
    name = u'poleno.pages'

    def ready(self):
        from . import checks
