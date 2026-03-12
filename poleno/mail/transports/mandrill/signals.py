# vim: expandtab
# -*- coding: utf-8 -*-
from base64 import b64decode

from django.core.files.base import ContentFile
from django.dispatch import Signal, receiver

from poleno.attachments.models import Attachment
from poleno.utils.mail import full_decode_header

from ...models import Message, Recipient


webhook_event = Signal()

@receiver(webhook_event)
def message_status_webhook_event(sender, event_type, data, **kwargs):
    if u'_id' not in data:
        return

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
        recipient = Recipient.objects.get(remote_id=data[u'_id'])
        recipient.status = status
        recipient.status_details = event_type
        recipient.save(update_fields=[u'status', u'status_details'])
    except (Recipient.DoesNotExist, Recipient.MultipleObjectsReturned):
        pass

@receiver(webhook_event)
def inbound_email_webhook_event(sender, event_type, data, **kwargs):
    if event_type == u'inbound' and u'msg' in data:
        msg = data[u'msg']
        headers = msg.get(u'headers') or ()
        from_name = msg.get(u'from_name') or u''
        from_mail = msg.get(u'from_email') or u''
        received_for = msg.get(u'email') or u''
        subject = msg.get(u'subject') or u''
        text = msg.get(u'text') or u''
        html = msg.get(u'html') or u''

        recipients = []
        for header_name, type in ((u'to', Recipient.TYPES.TO),
                                  (u'cc', Recipient.TYPES.CC),
                                  (u'bcc', Recipient.TYPES.BCC)):
            for rcp_mail, rcp_name in msg.get(header_name) or []:
                if rcp_mail:
                    recipients.append(Recipient(
                            name=rcp_name or u'',
                            mail=rcp_mail,
                            type=type,
                            status=Recipient.STATUSES.INBOUND,
                            ))

        attachments = []
        for attch in (msg.get(u'attachments') or {}).values():
            filename = attch.get(u'name') or u''
            filename = full_decode_header(filename) # Mandrill does not decode '=?utf-8?...?=' in attachment names.
            content = attch.get(u'content') or u''
            if attch.get(u'base64', False):
                content = b64decode(content)
            attachments.append(Attachment(
                    file=ContentFile(content),
                    name=filename,
                    ))

        message = Message(
                type=Message.TYPES.INBOUND,
                processed=None,
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
