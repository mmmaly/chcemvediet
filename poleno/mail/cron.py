# vim: expandtab
# -*- coding: utf-8 -*-
from django.conf import settings
from django.utils.module_loading import import_by_path

from poleno.cron import cron_job, cron_logger
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
                cron_logger.info(u'Received email: %s' % repr(message))

    # Process inbound mail; At most 10 messages in one batch
    messages = (Message.objects
            .inbound()
            .not_processed()
            .prefetch_related(Message.prefetch_recipients())
            )[:10]
    for message in messages:
        message.processed = utc_now()
        message.save()
        message_received.send(sender=None, message=message)
        cron_logger.info(u'Processed received email: %s' % repr(message))

    # Send outbound mail; At most 10 messages in one batch
    path = getattr(settings, u'EMAIL_OUTBOUND_TRANSPORT', None)
    if path:
        messages = (Message.objects
                .outbound()
                .not_processed()
                .prefetch_related(Message.prefetch_recipients())
                .prefetch_related(Message.prefetch_attachments())
                )[:10]
        if messages:
            klass = import_by_path(path)
            with klass() as transport:
                for message in messages:
                    transport.send_message(message)
                    message.processed = utc_now()
                    message.save()
                    message_sent.send(sender=None, message=message)
                    cron_logger.info(u'Sent email: %s' % repr(message))
