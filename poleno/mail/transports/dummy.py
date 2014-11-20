# vim: expandtab
# -*- coding: utf-8 -*-
from .base import BaseTransport

class DummyTransport(BaseTransport):
    def send_message(self, message):
        pass

    def get_messages(self):
        return []
