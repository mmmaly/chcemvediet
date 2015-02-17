# vim: expandtab
# -*- coding: utf-8 -*-
from django.apps import AppConfig

class AccountsConfig(AppConfig):
    name = u'chcemvediet.apps.accounts'

    def ready(self):
        from . import signals
