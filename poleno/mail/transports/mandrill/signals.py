# vim: expandtab
# -*- coding: utf-8 -*-
from django.dispatch import Signal, receiver

from ...models import Recipient

webhook_event = Signal(providing_args=['event_type', 'data'])

@receiver(webhook_event)
def message_webhook_event(sender, event_type, data, **kwargs):
    if event_type == u'deferral':
        status = Recipient.STATUSES.QUEUED
    elif event_type in [u'soft_bounce', u'hard_bounce', u'spam', u'reject']:
        status = Recipient.STATUSES.REJECTED
    elif event_type == u'send':
        status = Recipient.STATUSES.SENT
    elif event_type in [u'open', u'click']:
        status = Recipient.STATUSES.OPENED
    else:
        return

    try:
        recipient = Recipient.objects.get(remote_id=data['_id'])
        recipient.status = status
        recipient.status_details = event_type
        recipient.save()
    except (Recipient.DoesNotExist, Recipient.MultipleObjectsReturned):
        pass
