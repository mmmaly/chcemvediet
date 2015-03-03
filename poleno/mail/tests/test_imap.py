# vim: expandtab
# -*- coding: utf-8 -*-
import mock
import datetime
from textwrap import dedent

from django.conf import settings
from django.test import TestCase

from poleno.utils.date import utc_now
from poleno.utils.test import override_signals

from . import MailTestCaseMixin
from ..models import Message, Recipient
from ..cron import mail as mail_cron_job
from ..signals import message_sent, message_received

class ImapTransportTest(MailTestCaseMixin, TestCase):
    u"""
    Tests ``ImapTransport`` mail transport class.
    """

    def _create_mail(self, body=None, omit=(), headers={}):
        defaults = {
                u'Content-Type': u'multipart/mixed; boundary="===============1111111111=="',
                u'MIME-Version': u'1.0',
                u'Subject': u'Default Testing Subject',
                u'From': u'Default Testing From <default_testing_from@example.com>',
                u'To': u'Default Testing To <default_testing_to@example.com>',
                u'Cc': u'Default Testing Cc <default_testing_cc@a.com>',
                u'Date': u'Sat, 25 Oct 2014 22:32:52 -0000',
                u'Message-ID': u'<20141025223252.10450.74538@testhost>',
                u'X-Default-Testing-Extra-Header': u'Default Testing Value',
                }
        defaults.update(headers)
        for name in omit:
            del defaults[name]
        headers = u'\n'.join(u'%s: %s' % (name, value) for name, value in defaults.iteritems())
        if body is None:
            body = dedent(u"""\
                    --===============1111111111==
                    MIME-Version: 1.0
                    Content-Type: text/plain; charset="utf-8"
                    Content-Transfer-Encoding: 7bit

                    Default Testing Text Content
                    --===============1111111111==--""")
        return u'%s\n\n%s' % (headers, body)

    def _run_mail_cron_job(self, transport=None, ssl_transport=None, mails=[], delete_settings=(), **override_settings):
        overrides = {
                u'EMAIL_OUTBOUND_TRANSPORT': None,
                u'EMAIL_INBOUND_TRANSPORT': u'poleno.mail.transports.imap.ImapTransport',
                u'IMAP_SSL': False,
                u'IMAP_HOST': u'defaulttestinghost',
                u'IMAP_PORT': 1234,
                u'IMAP_USERNAME': u'defaulttestingusername',
                u'IMAP_PASSWORD': u'defaulttestingsecret',
                }
        overrides.update(override_settings)

        transport = mock.Mock()
        transport.return_value.search.return_value = [None, [u' '.join(str(k) for k in range(len(mails)))]]
        transport.return_value.fetch.side_effect = lambda k, _: [None, [[None, mails[int(k)]]]]
        imap4 = transport if not overrides[u'IMAP_SSL'] else None
        imap4ssl = transport if overrides[u'IMAP_SSL'] else None

        with self.settings(**overrides):
            for name in delete_settings:
                delattr(settings, name)
            with mock.patch.multiple(u'poleno.mail.transports.imap', IMAP4=imap4, IMAP4_SSL=imap4ssl):
                with override_signals(message_sent, message_received):
                    mail_cron_job().do()

        return transport


    def test_non_ssl_connect(self):
        transport = self._run_mail_cron_job(IMAP_SSL=False, IMAP_HOST=u'testhost.com', IMAP_PORT=2000)
        transport.assert_called_once_with(u'testhost.com', 2000)

    def test_non_ssl_connect_with_default_port(self):
        transport = self._run_mail_cron_job(IMAP_SSL=False, IMAP_HOST=u'testhost.com', delete_settings=[u'IMAP_PORT'])
        transport.assert_called_once_with(u'testhost.com', 143)

    def test_ssl_connect(self):
        transport = self._run_mail_cron_job(IMAP_SSL=True, IMAP_HOST=u'testhost.com', IMAP_PORT=2000)
        transport.assert_called_once_with(u'testhost.com', 2000)

    def test_ssl_connect_with_default_port(self):
        transport = self._run_mail_cron_job(IMAP_SSL=True, IMAP_HOST=u'testhost.com', delete_settings=[u'IMAP_PORT'])
        transport.assert_called_once_with(u'testhost.com', 993)

    def test_login(self):
        transport = self._run_mail_cron_job(IMAP_USERNAME=u'TestUser', IMAP_PASSWORD=u'big_secret')
        transport.return_value.login.assert_called_once_with(u'TestUser', u'big_secret')

    def test_transport_calls_with_empty_inbox(self):
        u"""
        Checks if imap methods are called in correct order.
        """
        transport = self._run_mail_cron_job(IMAP_HOST=u'testhost.com', IMAP_PORT=2000, IMAP_USERNAME=u'TestUser', IMAP_PASSWORD=u'big_secret')
        self.assertEqual(transport.mock_calls, [
            mock.call(u'testhost.com', 2000),
            mock.call().login(u'TestUser', u'big_secret'),
            mock.call().select(),
            mock.call().search(None, u'ALL'),
            mock.call().close(),
            mock.call().logout(),
            ])

    def test_transport_calls_with_nonempty_inbox(self):
        mails = [self._create_mail(), self._create_mail()]
        transport = self._run_mail_cron_job(mails=mails, IMAP_HOST=u'testhost.com', IMAP_PORT=2000, IMAP_USERNAME=u'TestUser', IMAP_PASSWORD=u'big_secret')
        self.assertEqual(transport.mock_calls, [
            mock.call(u'testhost.com', 2000),
            mock.call().login(u'TestUser', u'big_secret'),
            mock.call().select(),
            mock.call().search(None, u'ALL'),
            mock.call().fetch(u'0', '(RFC822)'),
            mock.call().store(u'0', u'+FLAGS', u'\\Deleted'),
            mock.call().fetch(u'1', '(RFC822)'),
            mock.call().store(u'1', u'+FLAGS', u'\\Deleted'),
            mock.call().expunge(),
            mock.call().close(),
            mock.call().logout(),
            ])

    def test_mail_stored_to_database_and_deleted_from_imap(self):
        mail = self._create_mail()
        transport = self._run_mail_cron_job(mails=[mail])
        transport.return_value.store.assert_called_once_with(u'0', u'+FLAGS', u'\\Deleted')
        self.assertEqual(Message.objects.count(), 1)

    def test_mail_stored_to_database_and_deleted_from_imap_with_multiple_mails_in_inbox(self):
        mails = [self._create_mail() for k in range(10)]
        transport = self._run_mail_cron_job(mails=mails)
        expected_calls = [mock.call(str(k), u'+FLAGS', u'\\Deleted') for k in range(10)]
        self.assertEqual(transport.return_value.store.mock_calls, expected_calls)
        self.assertEqual(Message.objects.count(), 10)

    def test_mail_marked_as_inbound(self):
        mail = self._create_mail()
        transport = self._run_mail_cron_job(mails=[mail])
        msg = Message.objects.first()
        self.assertEqual(msg.type, Message.TYPES.INBOUND)

    def test_mail_processed_date_ignoring_mail_date_header(self):
        mail = self._create_mail(headers={u'Date': u'Sat, 25 Oct 2014 22:32:52 -0000'})
        transport = self._run_mail_cron_job(mails=[mail])
        msg = Message.objects.first()
        self.assertAlmostEqual(msg.processed, utc_now(), delta=datetime.timedelta(seconds=10))

    def test_mail_subject_header(self):
        mail = self._create_mail(headers={u'Subject': u'Test Subject'})
        transport = self._run_mail_cron_job(mails=[mail])
        msg = Message.objects.first()
        self.assertEqual(msg.subject, u'Test Subject')

    def test_mail_with_encoded_subject_header(self):
        mail = self._create_mail(headers={u'Subject': u'GewSt: =?utf-8?q?_Wegfall_der_Vorl=C3=A4ufigkeit?='})
        transport = self._run_mail_cron_job(mails=[mail])
        msg = Message.objects.first()
        self.assertEqual(msg.subject, u'GewSt: Wegfall der Vorläufigkeit')

    def test_mail_with_invalid_subject_header(self):
        mail = self._create_mail(headers={u'Subject': u'GewSt: =?invalid?q?_Wegfall_der_Vorl=C3=A4ufigkeit?='})
        transport = self._run_mail_cron_job(mails=[mail])
        self.assertEqual(Message.objects.count(), 0)

    def test_mail_with_missing_subject_header(self):
        mail = self._create_mail(omit=[u'Subject'])
        transport = self._run_mail_cron_job(mails=[mail])
        msg = Message.objects.first()
        self.assertEqual(msg.subject, u'')

    def test_mail_from_header(self):
        mail = self._create_mail(headers={u'From': u'Agent Smith <smith@example.com>'})
        transport = self._run_mail_cron_job(mails=[mail])
        msg = Message.objects.first()
        self.assertEqual(msg.from_name, u'Agent Smith')
        self.assertEqual(msg.from_mail, u'smith@example.com')

    def test_mail_from_header_without_name(self):
        mail = self._create_mail(headers={u'From': u'smith@example.com'})
        transport = self._run_mail_cron_job(mails=[mail])
        msg = Message.objects.first()
        self.assertEqual(msg.from_name, u'')
        self.assertEqual(msg.from_mail, u'smith@example.com')

    def test_mail_with_missing_from_header(self):
        mail = self._create_mail(omit=[u'From'])
        transport = self._run_mail_cron_job(mails=[mail])
        msg = Message.objects.first()
        self.assertEqual(msg.from_name, u'')
        self.assertEqual(msg.from_mail, u'')

    def test_mail_received_for_field_is_undefined(self):
        mail = self._create_mail()
        transport = self._run_mail_cron_job(mails=[mail])
        msg = Message.objects.first()
        self.assertEqual(msg.received_for, u'')

    def test_mail_with_extra_header(self):
        mail = self._create_mail(headers={u'X-Something': u'Some value'})
        transport = self._run_mail_cron_job(mails=[mail])
        msg = Message.objects.first()
        self.assertIn(u'X-Something', msg.headers)
        self.assertEqual(msg.headers[u'X-Something'], u'Some value')

    def test_mail_to_cc_and_bcc_recipients(self):
        mail = self._create_mail(headers={
            u'To': u'Agent Smith <smith@example.com>',
            u'Cc': u'Cc Recipient1 <cc1@a.com>, Cc Recipient2 <cc2@a.com>',
            u'Bcc': u'Bcc Recipient <bcc@a.com>',
            })
        transport = self._run_mail_cron_job(mails=[mail])
        msg = Message.objects.first()
        self.assertEqual(msg.to_formatted, u'Agent Smith <smith@example.com>')
        self.assertEqual(msg.cc_formatted, u'Cc Recipient1 <cc1@a.com>, Cc Recipient2 <cc2@a.com>')
        self.assertEqual(msg.bcc_formatted, u'Bcc Recipient <bcc@a.com>')

    def test_mail_recipient_without_name(self):
        mail = self._create_mail(headers={
            u'To': u'smith@example.com',
            u'Cc': u'cc1@a.com, <cc2@a.com>',
            u'Bcc': u'bcc@a.com',
            })
        transport = self._run_mail_cron_job(mails=[mail])
        msg = Message.objects.first()
        self.assertEqual(msg.to_formatted, u'smith@example.com')
        self.assertEqual(msg.cc_formatted, u'cc1@a.com, cc2@a.com')
        self.assertEqual(msg.bcc_formatted, u'bcc@a.com')

    def test_mail_recipients_marked_as_inbound(self):
        mail = self._create_mail(headers={
            u'To': u'Agent Smith <smith@example.com>',
            u'Cc': u'Cc Recipient1 <cc1@a.com>, Cc Recipient2 <cc2@a.com>',
            u'Bcc': u'Bcc Recipient <bcc@a.com>',
            })
        transport = self._run_mail_cron_job(mails=[mail])
        msg = Message.objects.first()
        for rcpt in msg.recipient_set.all():
            self.assertEqual(rcpt.status, Recipient.STATUSES.INBOUND)

    def test_mail_with_text_body_only(self):
        mail = self._create_mail(body=dedent(u"""\
                --===============1111111111==
                MIME-Version: 1.0
                Content-Type: text/plain; charset="utf-8"
                Content-Transfer-Encoding: 7bit

                Text content
                --===============1111111111==--"""))
        transport = self._run_mail_cron_job(mails=[mail])
        msg = Message.objects.first()
        self.assertEqual(msg.text, u'Text content')
        self.assertEqual(msg.html, u'')
        self.assertEqual(msg.attachment_set.count(), 0)

    def test_mail_with_html_body_only(self):
        mail = self._create_mail(body=dedent(u"""\
                --===============1111111111==
                MIME-Version: 1.0
                Content-Type: text/html; charset="utf-8"
                Content-Transfer-Encoding: 7bit

                <p>HTML content</p>
                --===============1111111111==--"""))
        transport = self._run_mail_cron_job(mails=[mail])
        msg = Message.objects.first()
        self.assertEqual(msg.text, u'')
        self.assertEqual(msg.html, u'<p>HTML content</p>')
        self.assertEqual(msg.attachment_set.count(), 0)

    def test_mail_with_both_text_and_html_alternatives(self):
        mail = self._create_mail(body=dedent(u"""\
                --===============1111111111==
                Content-Type: multipart/alternative; boundary="===============2222222222=="
                MIME-Version: 1.0

                --===============2222222222==
                MIME-Version: 1.0
                Content-Type: text/plain; charset="utf-8"
                Content-Transfer-Encoding: 7bit

                Text content
                --===============2222222222==
                MIME-Version: 1.0
                Content-Type: text/html; charset="utf-8"
                Content-Transfer-Encoding: 7bit

                <p>HTML content</p>
                --===============2222222222==--
                --===============1111111111==--"""))
        transport = self._run_mail_cron_job(mails=[mail])
        msg = Message.objects.first()
        self.assertEqual(msg.text, u'Text content')
        self.assertEqual(msg.html, u'<p>HTML content</p>')
        self.assertEqual(msg.attachment_set.count(), 0)

    def test_mail_with_multiple_text_and_html_alternatives_stored_as_attachments(self):
        mail = self._create_mail(body=dedent(u"""\
                --===============1111111111==
                Content-Type: multipart/alternative; boundary="===============2222222222=="
                MIME-Version: 1.0

                --===============2222222222==
                MIME-Version: 1.0
                Content-Type: text/plain; charset="utf-8"
                Content-Transfer-Encoding: 7bit

                Text content 1
                --===============2222222222==
                MIME-Version: 1.0
                Content-Type: text/plain; charset="utf-8"
                Content-Transfer-Encoding: 7bit

                Text content 2
                --===============2222222222==
                MIME-Version: 1.0
                Content-Type: text/html; charset="utf-8"
                Content-Transfer-Encoding: 7bit

                <p>HTML content 1</p>
                --===============2222222222==
                MIME-Version: 1.0
                Content-Type: text/html; charset="utf-8"
                Content-Transfer-Encoding: 7bit

                <p>HTML content 2</p>
                --===============2222222222==--
                --===============1111111111==--"""))
        transport = self._run_mail_cron_job(mails=[mail])
        msg = Message.objects.first()
        attchs = msg.attachment_set.all()
        self.assertEqual(msg.text, u'Text content 1')
        self.assertEqual(msg.html, u'<p>HTML content 1</p>')
        self.assertEqual(len(attchs), 2)
        self.assertEqual(attchs[0].name, u'attachment.txt')
        self.assertEqual(attchs[0].content_type, u'text/plain')
        self.assertEqual(attchs[0].content, u'Text content 2')
        self.assertEqual(attchs[1].name, u'attachment.html')
        self.assertEqual(attchs[1].content_type, u'text/html')
        self.assertEqual(attchs[1].content, u'<p>HTML content 2</p>')

    def test_mail_with_attachment(self):
        mail = self._create_mail(body=dedent(u"""\
                --===============1111111111==
                MIME-Version: 1.0
                Content-Type: text/html; charset="utf-8"
                Content-Transfer-Encoding: 7bit

                <p>HTML content</p>
                --===============1111111111==
                MIME-Version: 1.0
                Content-Type: application/pdf
                Content-Transfer-Encoding: 7bit
                Content-Disposition: attachment; filename="filename.pdf"

                (content)
                --===============1111111111==--"""))
        transport = self._run_mail_cron_job(mails=[mail])
        msg = Message.objects.first()
        attchs = msg.attachment_set.all()
        self.assertEqual(len(attchs), 1)
        self.assertEqual(attchs[0].name, u'filename.pdf')
        self.assertEqual(attchs[0].content_type, u'application/pdf')
        self.assertEqual(attchs[0].content, u'(content)')

    def test_mail_with_attachment_without_filename(self):
        mail = self._create_mail(body=dedent(u"""\
                --===============1111111111==
                MIME-Version: 1.0
                Content-Type: text/html; charset="utf-8"
                Content-Transfer-Encoding: 7bit

                <p>HTML content</p>
                --===============1111111111==
                MIME-Version: 1.0
                Content-Type: application/pdf
                Content-Transfer-Encoding: 7bit

                (attachment content)
                --===============1111111111==--"""))
        transport = self._run_mail_cron_job(mails=[mail])
        msg = Message.objects.first()
        attchs = msg.attachment_set.all()
        self.assertEqual(len(attchs), 1)
        self.assertEqual(attchs[0].name, u'attachment.pdf')
        self.assertEqual(attchs[0].content_type, u'application/pdf')
        self.assertEqual(attchs[0].content, u'(attachment content)')

    def test_mail_without_text_body_but_with_text_attachment(self):
        u"""
        Checks that "text/plain" attachment is stored as an attachment even if there is no
        "text/plain" body in the email.
        """
        mail = self._create_mail(body=dedent(u"""\
                --===============1111111111==
                MIME-Version: 1.0
                Content-Type: text/html; charset="utf-8"
                Content-Transfer-Encoding: 7bit

                <p>HTML content</p>
                --===============1111111111==
                MIME-Version: 1.0
                Content-Type: text/plain
                Content-Transfer-Encoding: 7bit
                Content-Disposition: attachment; filename="filename.txt"

                (attachment content)
                --===============1111111111==--"""))
        transport = self._run_mail_cron_job(mails=[mail])
        msg = Message.objects.first()
        attchs = msg.attachment_set.all()
        self.assertEqual(msg.text, u'')
        self.assertEqual(msg.html, u'<p>HTML content</p>')
        self.assertEqual(len(attchs), 1)
        self.assertEqual(attchs[0].name, u'filename.txt')
        self.assertEqual(attchs[0].content_type, u'text/plain')
        self.assertEqual(attchs[0].content, u'(attachment content)')

    def test_mail_without_html_body_but_with_html_attachment(self):
        u"""
        Checks that "text/html" attachment is stored as an attachment even if there is no
        "text/html" body in the email.
        """
        mail = self._create_mail(body=dedent(u"""\
                --===============1111111111==
                MIME-Version: 1.0
                Content-Type: text/plain; charset="utf-8"
                Content-Transfer-Encoding: 7bit

                Text content
                --===============1111111111==
                MIME-Version: 1.0
                Content-Type: text/html
                Content-Transfer-Encoding: 7bit
                Content-Disposition: attachment; filename="filename.html"

                (attachment content)
                --===============1111111111==--"""))
        transport = self._run_mail_cron_job(mails=[mail])
        msg = Message.objects.first()
        attchs = msg.attachment_set.all()
        self.assertEqual(msg.text, u'Text content')
        self.assertEqual(msg.html, u'')
        self.assertEqual(len(attchs), 1)
        self.assertEqual(attchs[0].name, u'filename.html')
        self.assertEqual(attchs[0].content_type, u'text/html')
        self.assertEqual(attchs[0].content, u'(attachment content)')

    def test_mail_without_content_type_charset(self):
        mail = self._create_mail(body=dedent(u"""\
                --===============1111111111==
                MIME-Version: 1.0
                Content-Type: text/plain
                Content-Transfer-Encoding: 7bit

                Text content
                --===============1111111111==--"""))
        transport = self._run_mail_cron_job(mails=[mail])
        msg = Message.objects.first()
        self.assertEqual(msg.text, u'Text content')
        self.assertEqual(msg.html, u'')
        self.assertEqual(msg.attachment_set.count(), 0)

    def test_mail_with_invalid_content_type_charset(self):
        mail = self._create_mail(body=dedent(u"""\
                --===============1111111111==
                MIME-Version: 1.0
                Content-Type: text/plain; charset="invalid"
                Content-Transfer-Encoding: 7bit

                Text content
                --===============1111111111==--"""))
        transport = self._run_mail_cron_job(mails=[mail])
        self.assertEqual(Message.objects.count(), 0)
