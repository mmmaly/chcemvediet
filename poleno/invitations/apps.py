# vim: expandtab
# -*- coding: utf-8 -*-
from django.apps import AppConfig

class InvitationsConfig(AppConfig):
    name = u'poleno.invitations'

    def ready(self):
        from . import signals
