# vim: expandtab
# -*- coding: utf-8 -*-
from .base import BaseTransport

class DummyTransport(BaseTransport):
    def send_message(self, message):
        assert message.type == message.TYPES.OUTBOUND
        assert message.processed is None

        for recipient in message.recipients:
            recipient.status = recipient.STATUSES.SENT
            recipient.save()

    def get_messages(self):
        return []
