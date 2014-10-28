# vim: expandtab
# -*- coding: utf-8 -*-
from base64 import b64decode

from django.core.files.base import ContentFile
from django.dispatch import Signal, receiver

from poleno.attachments.models import Attachment
from poleno.utils.date import utc_now

from ...models import Message, Recipient
from ...signals import message_received

webhook_event = Signal(providing_args=['event_type', 'data'])

@receiver(webhook_event)
def message_status_webhook_event(sender, event_type, data, **kwargs):
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

@receiver(webhook_event)
def inbound_email_webhook_event(sender, event_type, data, **kwargs):
    if event_type == u'inbound' and u'msg' in data:
        msg = data[u'msg']
        headers = msg.get(u'headers', ())
        from_name = msg.get(u'from_name', u'')
        from_mail = msg.get(u'from_email', u'')
        received_for = msg.get(u'email', u'')
        subject = msg.get(u'subject', u'')
        text = msg.get(u'text', u'')
        html = msg.get(u'html', u'')

        recipients = []
        for header_name, type in ((u'to', Recipient.TYPES.TO),
                                  (u'cc', Recipient.TYPES.CC),
                                  (u'bcc', Recipient.TYPES.BCC)):
            for rcp_mail, rcp_name in msg.get(header_name, []):
                if rcp_mail:
                    recipients.append(Recipient(
                            name=rcp_name or u'',
                            mail=rcp_mail,
                            type=type,
                            status=Recipient.STATUSES.INBOUND,
                            ))

        attachments = []
        for attch in msg.get(u'attachments', {}).values():
            filename = attch.get(u'name', u'')
            content_type = attch.get(u'type', u'')
            content = attch.get(u'content', u'')
            if attch.get(u'base64', False):
                content = b64decode(content)
            attachments.append(Attachment(
                    file=ContentFile(content),
                    name=filename,
                    content_type=content_type,
                    ))

        message = Message(
                type=Message.TYPES.INBOUND,
                processed=utc_now(),
                from_name=from_name,
                from_mail=from_mail,
                received_for=received_for,
                subject=subject,
                text=text,
                html=html,
                headers=headers,
                )
        message.save()

        for recipient in recipients:
            recipient.message = message
            recipient.save()

        for attachment in attachments:
            attachment.generic_object = message
            attachment.save()

        message_received.send(sender=None, message=message)
