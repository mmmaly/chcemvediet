# vim: expandtab
# -*- coding: utf-8 -*-
from email.mime.text import MIMEText
from django.core.mail import EmailMessage, EmailMultiAlternatives
from django.test import TestCase

from . import MailTestCaseMixin
from ..models import Message, Recipient

class EmailBackendTest(MailTestCaseMixin, TestCase):
    u"""
    Tests ``EmailBackend`` email backend class.
    """

    def _send_email(self, **kwargs):
        content_subtype = kwargs.pop(u'content_subtype', None)
        alternatives = kwargs.pop(u'alternatives', None)
        constructor = EmailMessage if alternatives is None else EmailMultiAlternatives
        mail = self._call_with_defaults(constructor, kwargs, {
            u'subject': u'Subject',
            u'body': u'content',
            u'from_email': 'from@example.com',
            u'to': [u'to@example.com'],
            })
        if content_subtype is not None:
            mail.content_subtype = content_subtype
        if alternatives is not None:
            for content, content_type in alternatives:
                mail.attach_alternative(content, content_type)
        mail.send()
        return mail


    def test_message_instance_created(self):
        mail = self._send_email()
        self.assertIsInstance(mail.instance, Message)
        self.assertIsNotNone(mail.instance.pk)
        result = Message.objects.get(pk=mail.instance.pk)
        self.assertEqual(result, mail.instance)

    def test_message_type_is_outbound(self):
        mail = self._send_email()
        self.assertEqual(mail.instance.type, Message.TYPES.OUTBOUND)

    def test_message_is_queued(self):
        mail = self._send_email()
        self.assertIsNone(mail.instance.processed)

    def test_message_from_email(self):
        mail = self._send_email(from_email=u'John Smith <johnsmith@example.com>')
        self.assertEqual(mail.instance.from_name, u'John Smith')
        self.assertEqual(mail.instance.from_mail, u'johnsmith@example.com')

    def test_message_from_email_with_empty_name(self):
        mail = self._send_email(from_email=u'johnsmith@example.com')
        self.assertEqual(mail.instance.from_name, u'')
        self.assertEqual(mail.instance.from_mail, u'johnsmith@example.com')

    def test_message_with_default_from_email_if_ommited(self):
        with self.settings(DEFAULT_FROM_EMAIL=u'Default <default@example.com>'):
            mail = self._send_email(_omit=[u'from_email'])
        self.assertEqual(mail.instance.from_name, u'Default')
        self.assertEqual(mail.instance.from_mail, u'default@example.com')

    def test_message_received_for_is_empty(self):
        mail = self._send_email()
        self.assertEqual(mail.instance.received_for, u'')

    def test_message_subject(self):
        mail = self._send_email(subject=u'Mail Subject')
        self.assertEqual(mail.instance.subject, u'Mail Subject')

    def test_message_extra_headers(self):
        mail = self._send_email(headers={u'X-Some-Header': u'Some Value', u'X-Another-Header': u'Another Value'})
        self.assertEqual(mail.instance.headers, {u'X-Some-Header': u'Some Value', u'X-Another-Header': u'Another Value'})

    def test_message_recipients(self):
        mail = self._send_email(to=[u'Name <to1@a.com>', u'to2@a.com'], cc=[u'cc1@a.com', u'cc2@a.com'], bcc=[u'bcc@a.com'])
        self.assertEqual(mail.instance.to_formatted, u'Name <to1@a.com>, to2@a.com')
        self.assertEqual(mail.instance.cc_formatted, u'cc1@a.com, cc2@a.com')
        self.assertEqual(mail.instance.bcc_formatted, u'bcc@a.com')

    def test_message_recipients_have_queued_status(self):
        mail = self._send_email(to=[u'Name <to1@a.com>', u'to2@a.com'], cc=[u'cc1@a.com', u'cc2@a.com'], bcc=[u'bcc@a.com'])
        for rcpt in mail.instance.recipient_set.all():
            self.assertEqual(rcpt.status, Recipient.STATUSES.QUEUED)

    def test_message_recipients_have_empty_status_details_and_remote_id(self):
        mail = self._send_email(to=[u'Name <to1@a.com>', u'to2@a.com'], cc=[u'cc1@a.com', u'cc2@a.com'], bcc=[u'bcc@a.com'])
        for rcpt in mail.instance.recipient_set.all():
            self.assertEqual(rcpt.status_details, u'')
            self.assertEqual(rcpt.remote_id, u'')

    def test_message_with_text_body(self):
        mail = self._send_email(body=u'Text content')
        self.assertEqual(mail.instance.text, u'Text content')
        self.assertEqual(mail.instance.html, u'')
        self.assertEqual(list(mail.instance.attachment_set.all()), [])

    def test_message_with_html_body(self):
        mail = self._send_email(body=u'<p>HTML content</p>', content_subtype=u'html')
        self.assertEqual(mail.instance.text, u'')
        self.assertEqual(mail.instance.html, u'<p>HTML content</p>')
        self.assertEqual(list(mail.instance.attachment_set.all()), [])

    def test_message_with_text_body_and_html_alternative(self):
        mail = self._send_email(body=u'Text content', alternatives=[
            (u'<p>HTML alternative</p>', u'text/html'),
            ])
        self.assertEqual(mail.instance.text, u'Text content')
        self.assertEqual(mail.instance.html, u'<p>HTML alternative</p>')
        self.assertEqual(list(mail.instance.attachment_set.all()), [])

    def test_message_with_html_body_and_text_alternative(self):
        mail = self._send_email(body=u'<p>HTML content</p>', content_subtype=u'html', alternatives=[
            (u'Plain alternative', u'text/plain'),
            ])
        self.assertEqual(mail.instance.text, u'Plain alternative')
        self.assertEqual(mail.instance.html, u'<p>HTML content</p>')
        self.assertEqual(list(mail.instance.attachment_set.all()), [])

    def test_message_with_text_body_and_multiple_alternatives(self):
        mail = self._send_email(body=u'Text content', alternatives=[
            (u'<p>HTML alternative 1</p>', u'text/html'),
            (u'<p>HTML alternative 2</p>', u'text/html'),
            (u'Text alternative', u'text/plain'),
            ])
        self.assertEqual(mail.instance.text, u'Text content')
        self.assertEqual(mail.instance.html, u'<p>HTML alternative 1</p>')
        attachments = [(a.name, a.content, a.content_type) for a in mail.instance.attachment_set.all()]
        self.assertEqual(attachments, [
            (u'message.html', u'<p>HTML alternative 2</p>', u'text/html'),
            (u'message.txt', u'Text alternative', u'text/plain'),
            ])

    def test_message_with_html_body_and_multiple_alternatives(self):
        mail = self._send_email(body=u'<p>HTML content</p>', content_subtype=u'html', alternatives=[
            (u'<p>HTML alternative</p>', u'text/html'),
            (u'Text alternative 1', u'text/plain'),
            (u'Text alternative 2', u'text/plain'),
            ])
        self.assertEqual(mail.instance.text, u'Text alternative 1')
        self.assertEqual(mail.instance.html, u'<p>HTML content</p>')
        attachments = [(a.name, a.content, a.content_type) for a in mail.instance.attachment_set.all()]
        self.assertEqual(attachments, [
            (u'message.html', u'<p>HTML alternative</p>', u'text/html'),
            (u'message.txt', u'Text alternative 2', u'text/plain'),
            ])

    def test_message_with_attachments_as_tuples(self):
        mail = self._send_email(attachments=[
            (u'filename.pdf', u'(pdf content)', u'application/pdf'),
            (u'another.txt', u'text attachment', u'text/plain'),
            ])
        attachments = [(a.name, a.content, a.content_type) for a in mail.instance.attachment_set.all()]
        self.assertEqual(attachments, [
            (u'filename.pdf', u'(pdf content)', u'application/pdf'),
            (u'another.txt', u'text attachment', u'text/plain'),
            ])

    def test_message_with_attachment_as_tuple_with_missing_filename_and_content_type(self):
        mail = self._send_email(attachments=[
            (None, u'content', None),
            ])
        attachments = [(a.name, a.content, a.content_type) for a in mail.instance.attachment_set.all()]
        self.assertEqual(attachments, [
            (u'attachment.bin', u'content', u'application/octet-stream'),
            ])

    def test_message_with_attachment_as_mime_object(self):
        mail = self._send_email(attachments=[MIMEText(u'text attachment')])
        attachments = [(a.name, a.content, a.content_type) for a in mail.instance.attachment_set.all()]
        self.assertEqual(attachments, [
            (u'attachment.txt', u'text attachment', u'text/plain'),
            ])

    def test_message_with_attachments_and_multiple_alternatives(self):
        mail = self._send_email(body=u'Text content', alternatives=[
            (u'<p>HTML alternative 1</p>', u'text/html'),
            (u'<p>HTML alternative 2</p>', u'text/html'),
            (u'Text alternative', u'text/plain'),
            ], attachments=[
            (u'filename.pdf', u'(pdf content)', u'application/pdf'),
            (u'another.txt', u'text attachment', u'text/plain'),
            ])
        self.assertEqual(mail.instance.text, u'Text content')
        self.assertEqual(mail.instance.html, u'<p>HTML alternative 1</p>')
        attachments = [(a.name, a.content, a.content_type) for a in mail.instance.attachment_set.all()]
        self.assertEqual(attachments, [
            (u'filename.pdf', u'(pdf content)', u'application/pdf'),
            (u'another.txt', u'text attachment', u'text/plain'),
            (u'message.html', u'<p>HTML alternative 2</p>', u'text/html'),
            (u'message.txt', u'Text alternative', u'text/plain'),
            ])
