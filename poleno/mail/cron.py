# vim: expandtab
# -*- coding: utf-8 -*-
from django.conf import settings
from django.utils.module_loading import import_by_path

from poleno.cron import cron_job
from poleno.utils.date import utc_now

from .models import Message
from .signals import message_sent, message_received

@cron_job(run_every_mins=1)
def mail():
    # Get inbound mail
    path = getattr(settings, u'EMAIL_INBOUND_TRANSPORT', None)
    if path:
        klass = import_by_path(path)
        with klass() as transport:
            for message in transport.get_messages():
                print(u'Received email: %s' % repr(message))

    # Process inbound mail
    messages = Message.objects.inbound().not_processed()[:10] # At most 10 messages in one batch
    for message in messages:
        print(u'Processing received email: %s...' % repr(message))
        message.processed = utc_now()
        message.save()
        message_received.send(sender=None, message=message)
        print(u'Done.')

    # Send outbound mail
    path = getattr(settings, u'EMAIL_OUTBOUND_TRANSPORT', None)
    if path:
        messages = Message.objects.outbound().not_processed()[:10] # At most 10 messages in one batch
        if messages:
            klass = import_by_path(path)
            with klass() as transport:
                for message in messages:
                    print(u'Sending email: %s...' % repr(message))
                    transport.send_message(message)
                    message.processed = utc_now()
                    message.save()
                    message_sent.send(sender=None, message=message)
                    print(u'Done.')
