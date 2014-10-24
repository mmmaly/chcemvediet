# vim: expandtab
# -*- coding: utf-8 -*-
from email.utils import parseaddr
from email.mime.base import MIMEBase

from django.core.files.base import ContentFile
from django.core.mail.message import sanitize_address, DEFAULT_ATTACHMENT_MIME_TYPE
from django.core.mail.backends.base import BaseEmailBackend

from poleno.utils.misc import guess_extension
from poleno.attachments.models import Attachment

from .models import Message, Recipient

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
        text = message.body if message.content_subtype != u'html' else None
        html = message.body if message.content_subtype == u'html' else None
        headers = message.extra_headers

        # We may have only one plaintext and one html message body. If the message has more
        # plaintext and/or html aternatives, they are converted to attachments.
        remnant_alternatives = []
        for content, content_type in getattr(message, u'alternatives', []):
            if content_type == u'text/plain' and text is None:
                text = content
            elif content_type == u'text/html' and html is None:
                html = content
            else:
                ext = guess_extension(content_type, u'.bin')
                remnant_alternatives.append((u'message%s' % ext, content, content_type))

        recipients = []
        for addresses, type in ((message.to, Recipient.TYPES.TO),
                                (message.cc, Recipient.TYPES.CC),
                                (message.bcc, Recipient.TYPES.BCC)):
            for addr in addresses:
                sanitized = sanitize_address(addr, message.encoding)
                name, mail = parseaddr(sanitized)
                recipients.append(Recipient(
                        name=name,
                        mail=mail,
                        type=type,
                        status=Recipient.STATUSES.QUEUED,
                        ))

        attachments = []
        for attachment in message.attachments + remnant_alternatives:
            if isinstance(attachment, MIMEBase):
                name = attachment.get_filename()
                content = attachment.get_payload(decode=True)
                content_type = attachment.get_content_type()
            else:
                name, content, content_type = attachment
            if not content_type:
                content_type = DEFAULT_ATTACHMENT_MIME_TYPE
            if not name:
                name = u'attachment%s' % guess_extension(content_type, u'.bin')
            attachments.append(Attachment(
                    file=ContentFile(content),
                    name=name,
                    content_type=content_type,
                    ))

        msg = Message(
                type=Message.TYPES.OUTBOUND,
                from_name=from_name,
                from_mail=from_mail,
                subject=subject,
                text=text or u'',
                html=html or u'',
                headers=headers,
                )
        msg.save()
        message.instance = msg

        for recipient in recipients:
            recipient.message = msg
            recipient.save()

        for attachment in attachments:
            attachment.generic_object = msg
            attachment.save()
