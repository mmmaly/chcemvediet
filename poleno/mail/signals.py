# vim: expandtab
# -*- coding: utf-8 -*-
from django.dispatch.dispatcher import Signal

message_sent = Signal(providing_args=['message'])
message_received = Signal(providing_args=['message'])
