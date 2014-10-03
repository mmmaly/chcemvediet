# vim: expandtab
# -*- coding: utf-8 -*-
from email.utils import parseaddr
from email.mime.base import MIMEBase

from django.core.files.base import ContentFile
from django.core.mail.message import sanitize_address, DEFAULT_ATTACHMENT_MIME_TYPE
from django.core.mail.backends.base import BaseEmailBackend

from models import Message, Recipient, Attachment

class EmailBackend(BaseEmailBackend):

    def send_messages(self, email_messages):
        for message in email_messages:
            self._enqueue(message)
        return len(email_messages)

    def _enqueue(self, message):
        # Based on djrill.mail.backends.DjrillBackend; We can't use Djrill directly because it
        # sends the mail synchronously during user requests.
        sanitized = sanitize_address(message.from_email, message.encoding)
        from_name, from_mail = parseaddr(sanitized)

        subject = message.subject
        text = message.body if message.content_subtype != u'html' else u''
        html = message.body if message.content_subtype == u'html' else u''
        headers = message.extra_headers

        if getattr(message, u'alternatives', None):
            if len(message.alternatives) > 1:
                raise ValueError(u'Too many alternatives attached to the message.')
            content, mimetype = message.alternatives[0]
            if mimetype != u'text/html':
                raise ValueError(u'Invalid alternative mimetype "%s".' % mimetype)
            if message.content_subtype == u'html':
                raise ValueError(u'Alternative with the same mimetype as the body.')
            html = content

        msg = Message(
                type=Message.TYPES.OUTBOUND,
                from_name=from_name,
                from_mail=from_mail,
                subject=subject,
                text=text,
                html=html,
                headers=headers,
                )
        msg.save()

        for addresses, type in ((message.to, Recipient.TYPES.TO),
                                (message.cc, Recipient.TYPES.CC),
                                (message.bcc, Recipient.TYPES.BCC)):
            for addr in addresses:
                sanitized = sanitize_address(addr, message.encoding)
                name, mail = parseaddr(sanitized)

                recipient = Recipient(
                        message=msg,
                        name=name,
                        mail=mail,
                        type=type,
                        status=Recipient.STATUSES.QUEUED,
                        )
                recipient.save()

        for attachment in message.attachments:
            if isinstance(attachment, MIMEBase):
                name = attachment.get_filename()
                content = attachment.get_payload(decode=True)
                content_type = attachment.get_content_type()
            else:
                name, content, content_type = attachment

            attch = Attachment(
                    message=msg,
                    file=ContentFile(content),
                    name=name,
                    content_type=content_type or DEFAULT_ATTACHMENT_MIME_TYPE,
                    )
            attch.save()
