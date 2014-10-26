# vim: expandtab
# -*- coding: utf-8 -*-
import email
import email.header
import email.message
from email.utils import parseaddr
from imaplib import IMAP4, IMAP4_SSL, IMAP4_PORT, IMAP4_SSL_PORT

from django.core.files.base import ContentFile
from django.conf import settings

from poleno.attachments.models import Attachment
from poleno.utils.date import utc_now
from poleno.utils.misc import guess_extension

from .base import BaseTransport
from ..models import Message, Recipient

class ImapTransport(BaseTransport):
    def __init__(self, **kwargs):
        super(ImapTransport, self).__init__(**kwargs)
        self.ssl = getattr(settings, u'IMAP_SSL', False)
        self.host = getattr(settings, u'IMAP_HOST', u'')
        self.port = getattr(settings, u'IMAP_PORT', IMAP4_SSL_PORT if self.ssl else IMAP4_PORT)
        self.username = getattr(settings, u'IMAP_USERNAME', u'')
        self.password = getattr(settings, u'IMAP_PASSWORD', u'')
        self.transport = IMAP4_SSL if self.ssl else IMAP4
        self.connection = None

    def connect(self):
        self.connection = self.transport(self.host, self.port)
        self.connection.login(self.username, self.password)
        self.connection.select()

    def disconnect(self):
        self.connection.close()
        self.connection.logout()
        self.connection = None

    def _decode_content(self, content, charset):
        try:
            decoded = content.decode(charset, u'replace') if charset else content
            return decoded
        except LookupError as e:
            raise email.errors.MessageParseError(e)

    def _decode_header(self, header):
        parts = email.header.decode_header(header)
        try:
            decoded = u''.join(unicode(part, enc or u'ASCII', u'replace') for part, enc in parts)
            return decoded
        except LookupError as e:
            raise email.errors.MessageParseError(e)

    def _decode_message(self, msg):
        assert isinstance(msg, email.message.Message)

        headers = {name: self._decode_header(value) for name, value in msg.items()}
        subject = self._decode_header(msg.get(u'subject', u''))
        from_header = self._decode_header(msg.get(u'from', u''))
        from_name, from_mail = parseaddr(from_header)

        text = u''
        html = u''
        attachments = []
        for part in msg.walk():
            if part.is_multipart():
                continue
            content_type = part.get_content_type()
            charset = part.get_content_charset()
            content = part.get_payload(decode=True)
            disposition = self._decode_header(part.get(u'Content-Disposition', u''))
            is_attachment = disposition.startswith(u'attachment')
            if not text and content_type == u'text/plain' and not is_attachment:
                text = self._decode_content(content, charset)
            elif not html and content_type == u'text/html' and not is_attachment:
                html = self._decode_content(content, charset)
            else:
                default = u'attachment%s' % guess_extension(content_type, u'.bin')
                filename = part.get_filename(default)
                attachments.append(Attachment(
                        file=ContentFile(content),
                        name=filename,
                        content_type=content_type,
                        ))

        recipients = []
        for header_name, type in ((u'to', Recipient.TYPES.TO),
                                  (u'cc', Recipient.TYPES.CC),
                                  (u'bcc', Recipient.TYPES.BCC)):
            header = self._decode_header(msg.get(header_name, u''))
            for rcp_address in header.split(','):
                rcp_name, rcp_mail = parseaddr(rcp_address)
                if rcp_mail:
                    recipients.append(Recipient(
                            name=rcp_name,
                            mail=rcp_mail,
                            type=type,
                            status=Recipient.STATUSES.INBOUND,
                            ))

        message = Message(
                type=Message.TYPES.INBOUND,
                processed=utc_now(),
                from_name=from_name,
                from_mail=from_mail,
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

        return message

    def get_message(self):
        # Based on django_mailbox.transports.imap.ImapTransport
        _, inbox = self.connection.search(None, u'ALL')
        if inbox[0]:
            for key in inbox[0].split():
                try:
                    _, contents = self.connection.fetch(key, '(RFC822)')
                    msg = email.message_from_string(contents[0][1])
                    message = self._decode_message(msg)
                except email.errors.MessageParseError:
                    continue

                yield message

                self.connection.store(key, u'+FLAGS', u'\\Deleted')
            self.connection.expunge()
