# vim: expandtab
# -*- coding: utf-8 -*-
import mock
from textwrap import dedent
from collections import defaultdict

from django.core.mail import BadHeaderError
from django.test import TestCase

from poleno.timewarp import timewarp
from poleno.utils.date import local_datetime_from_utc
from poleno.utils.misc import Bunch
from poleno.utils.test import override_signals

from . import MailTestCaseMixin
from ..models import Message, Recipient
from ..cron import mail as mail_cron_job
from ..signals import message_sent, message_received

class SmtpTransportTest(MailTestCaseMixin, TestCase):
    u"""
    Tests ``SmtpTransport`` mail transport class.
    """

    def _create_message(self, **kwargs):
        kwargs.setdefault(u'type', Message.TYPES.OUTBOUND)
        kwargs.setdefault(u'processed', None)
        return super(SmtpTransportTest, self)._create_message(**kwargs)

    def _create_recipient(self, **kwargs):
        kwargs.setdefault(u'status', Recipient.STATUSES.QUEUED)
        return super(SmtpTransportTest, self)._create_recipient(**kwargs)

    def _parse_headers(self, headers):
        dd = defaultdict(list)
        for header in headers.split(u'\n'):
            key, value = header.split(u': ', 1)
            dd[key].append(value)
        res = {k: v for k, v in dd.iteritems()}
        return res

    def _run_mail_cron_job(self):
        connection = mock.Mock()
        with self.settings(EMAIL_OUTBOUND_TRANSPORT=u'poleno.mail.transports.smtp.SmtpTransport', EMAIL_INBOUND_TRANSPORT=None):
            with mock.patch(u'poleno.mail.transports.smtp.get_connection', return_value=connection):
                with override_signals(message_sent, message_received):
                    mail_cron_job().do()
        res = []
        for call in connection.send_messages.call_args_list:
            for mail in call[0][0]:
                as_bytes = mail.message().as_bytes()
                headers, body = as_bytes.split(u'\n\n', 1)
                headers = self._parse_headers(headers)
                res.append(Bunch(headers=headers, body=body, as_bytes=as_bytes))
        return res


    def test_message_send_date(self):
        timewarp.enable()
        timewarp.jump(local_datetime_from_utc(u'2010-10-05 10:13:35'))
        msg = self._create_message()
        rcpt = self._create_recipient(message=msg)
        result = self._run_mail_cron_job()
        self.assertEqual(result[0].headers[u'Date'], [u'Tue, 05 Oct 2010 10:13:35 -0000'])
        timewarp.reset()

    def test_message_from_name_and_from_mail(self):
        msg = self._create_message(from_name=u'John Smith', from_mail=u'smith@example.com')
        rcpt = self._create_recipient(message=msg)
        result = self._run_mail_cron_job()
        self.assertEqual(result[0].headers[u'From'], [u'John Smith <smith@example.com>'])

    def test_message_with_from_name_with_comma(self):
        msg = self._create_message(from_name=u'Smith, John', from_mail=u'smith@example.com')
        rcpt = self._create_recipient(message=msg)
        result = self._run_mail_cron_job()
        self.assertEqual(result[0].headers[u'From'], [u'"Smith, John" <smith@example.com>'])

    def test_message_with_empty_from_name(self):
        msg = self._create_message(from_mail=u'smith@example.com', omit=[u'from_name'])
        rcpt = self._create_recipient(message=msg)
        result = self._run_mail_cron_job()
        self.assertEqual(result[0].headers[u'From'], [u'smith@example.com'])

    def test_message_with_default_from_mail_if_both_from_name_and_from_mail_are_empty(self):
        msg = self._create_message(omit=[u'from_name', u'from_mail'])
        rcpt = self._create_recipient(message=msg)
        with self.settings(DEFAULT_FROM_EMAIL=u'Default <default@example.com>'):
            result = self._run_mail_cron_job()
        self.assertEqual(result[0].headers[u'From'], [u'Default <default@example.com>'])

    def test_message_subject(self):
        msg = self._create_message(subject=u'Mail Subject')
        rcpt = self._create_recipient(message=msg)
        result = self._run_mail_cron_job()
        self.assertEqual(result[0].headers[u'Subject'], [u'Mail Subject'])

    def test_message_with_empty_subject(self):
        msg = self._create_message(omit=[u'subject'])
        rcpt = self._create_recipient(message=msg)
        result = self._run_mail_cron_job()
        self.assertEqual(result[0].headers[u'Subject'], [u''])

    def test_message_with_subject_with_linebreak_raises_exception(self):
        msg = self._create_message(subject=u'Subject\nwith\nnew\nlines')
        rcpt = self._create_recipient(message=msg)
        with self.assertRaisesMessage(BadHeaderError, u"Header values can't contain newlines"):
            result = self._run_mail_cron_job()

    def test_message_with_text_body_only(self):
        msg = self._create_message(text=u'Text content', omit=[u'html'])
        rcpt = self._create_recipient(message=msg)
        result = self._run_mail_cron_job()
        self.assertRegexpMatches(result[0].headers[u'Content-Type'][0], u'multipart/mixed; boundary="===============.*=="')
        self.assertRegexpMatches(result[0].body, dedent(u"""\
                --===============.*==
                MIME-Version: 1.0
                Content-Type: text/plain; charset="utf-8"
                Content-Transfer-Encoding: 7bit

                Text content
                --===============.*==--"""))

    def test_message_with_html_body_only(self):
        msg = self._create_message(html=u'<p>HTML content</p>', omit=[u'text'])
        rcpt = self._create_recipient(message=msg)
        result = self._run_mail_cron_job()
        self.assertRegexpMatches(result[0].headers[u'Content-Type'][0], u'multipart/mixed; boundary="===============.*=="')
        self.assertRegexpMatches(result[0].body, dedent(u"""\
                --===============.*==
                MIME-Version: 1.0
                Content-Type: text/html; charset="utf-8"
                Content-Transfer-Encoding: 7bit

                <p>HTML content</p>
                --===============.*==--"""))

    def test_message_with_both_text_and_html_body(self):
        msg = self._create_message(text=u'Text content', html=u'<p>HTML content</p>')
        rcpt = self._create_recipient(message=msg)
        result = self._run_mail_cron_job()
        self.assertRegexpMatches(result[0].headers[u'Content-Type'][0], u'multipart/mixed; boundary="===============.*=="')
        self.assertRegexpMatches(result[0].body, dedent(u"""\
                --===============.*==
                Content-Type: multipart/alternative; boundary="===============.*=="
                MIME-Version: 1.0

                --===============.*==
                MIME-Version: 1.0
                Content-Type: text/plain; charset="utf-8"
                Content-Transfer-Encoding: 7bit

                Text content
                --===============.*==
                MIME-Version: 1.0
                Content-Type: text/html; charset="utf-8"
                Content-Transfer-Encoding: 7bit

                <p>HTML content</p>
                --===============.*==--
                --===============.*==--"""))

    def test_message_with_neither_text_nor_html_body(self):
        msg = self._create_message(omit=[u'text', u'html'])
        rcpt = self._create_recipient(message=msg)
        result = self._run_mail_cron_job()
        self.assertRegexpMatches(result[0].headers[u'Content-Type'][0], u'multipart/mixed; boundary="===============.*=="')
        self.assertRegexpMatches(result[0].body, dedent(u"""\
                --===============.*==

                --===============.*==--"""))

    def test_message_with_extra_headers(self):
        msg = self._create_message(headers={u'X-Some-Header': u'Value', u'X-Another-Header': u'Another Value'})
        rcpt = self._create_recipient(message=msg)
        result = self._run_mail_cron_job()
        self.assertEqual(result[0].headers[u'X-Some-Header'], [u'Value'])
        self.assertEqual(result[0].headers[u'X-Another-Header'], [u'Another Value'])

    def test_message_with_attachments(self):
        msg = self._create_message(text=u'Text content', html=u'<p>HTML content</p>')
        rcpt = self._create_recipient(message=msg)
        attch1 = self._create_attachment(generic_object=msg, content=u'content', name=u'filename.txt', content_type=u'text/plain')
        attch2 = self._create_attachment(generic_object=msg, content=u'<p>content</p>', name=u'filename.html', content_type=u'text/html')
        result = self._run_mail_cron_job()
        self.assertRegexpMatches(result[0].headers[u'Content-Type'][0], u'multipart/mixed; boundary="===============.*=="')
        self.assertRegexpMatches(result[0].body, dedent(u"""\
                --===============.*==
                Content-Type: multipart/alternative; boundary="===============.*=="
                MIME-Version: 1.0

                --===============.*==
                MIME-Version: 1.0
                Content-Type: text/plain; charset="utf-8"
                Content-Transfer-Encoding: 7bit

                Text content
                --===============.*==
                MIME-Version: 1.0
                Content-Type: text/html; charset="utf-8"
                Content-Transfer-Encoding: 7bit

                <p>HTML content</p>
                --===============.*==--
                --===============.*==
                MIME-Version: 1.0
                Content-Type: text/plain; charset="utf-8"
                Content-Transfer-Encoding: 7bit
                Content-Disposition: attachment; filename="filename.txt"

                content
                --===============.*==
                MIME-Version: 1.0
                Content-Type: text/html; charset="utf-8"
                Content-Transfer-Encoding: 7bit
                Content-Disposition: attachment; filename="filename.html"

                <p>content</p>
                --===============.*==--"""))

    def test_message_with_to_and_cc_recipients(self):
        msg = self._create_message()
        to1 = self._create_recipient(message=msg, name=u'To Recipient1', mail=u'to1@a.com', type=Recipient.TYPES.TO)
        to2 = self._create_recipient(message=msg, name=u'To Recipient2', mail=u'to2@a.com', type=Recipient.TYPES.TO)
        cc1 = self._create_recipient(message=msg, name=u'Cc Recipient1', mail=u'cc1@a.com', type=Recipient.TYPES.CC)
        cc2 = self._create_recipient(message=msg, name=u'Cc Recipient2', mail=u'cc2@a.com', type=Recipient.TYPES.CC)
        result = self._run_mail_cron_job()
        self.assertEqual(result[0].headers[u'To'], [u'To Recipient1 <to1@a.com>, To Recipient2 <to2@a.com>'])
        self.assertEqual(result[0].headers[u'Cc'], [u'Cc Recipient1 <cc1@a.com>, Cc Recipient2 <cc2@a.com>'])

    def test_message_with_recipient_with_comma_in_name(self):
        msg = self._create_message()
        to = self._create_recipient(message=msg, name=u'Smith, John', mail=u'smith@example.com', type=Recipient.TYPES.TO)
        result = self._run_mail_cron_job()
        self.assertEqual(result[0].headers[u'To'], [u'"Smith, John" <smith@example.com>'])

    def test_message_with_recipient_with_quote_in_name(self):
        msg = self._create_message()
        to = self._create_recipient(message=msg, name=u'John "Agent" Smith', mail=u'smith@example.com', type=Recipient.TYPES.TO)
        result = self._run_mail_cron_job()
        self.assertEqual(result[0].headers[u'To'], [u'"John \\"Agent\\" Smith" <smith@example.com>'])

    def test_message_with_recipient_without_name(self):
        msg = self._create_message()
        to = self._create_recipient(message=msg, mail=u'smith@example.com', type=Recipient.TYPES.TO, omit=[u'name'])
        result = self._run_mail_cron_job()
        self.assertEqual(result[0].headers[u'To'], [u'smith@example.com'])

    def test_message_has_bcc_recipient_hidden(self):
        msg = self._create_message()
        to = self._create_recipient(message=msg, name=u'John Smith', mail=u'smith@example.com', type=Recipient.TYPES.TO)
        bcc = self._create_recipient(message=msg, name=u'Bcc Recipient', mail=u'bcc@example.com', type=Recipient.TYPES.BCC)
        result = self._run_mail_cron_job()
        self.assertEqual(result[0].headers[u'To'], [u'John Smith <smith@example.com>'])
        self.assertNotIn(u'Bcc Recipient', result[0].as_bytes)
        self.assertNotIn(u'bcc@example.com', result[0].as_bytes)

    def test_message_with_only_bcc_recipient(self):
        msg = self._create_message()
        bcc = self._create_recipient(message=msg, name=u'Bcc Recipient', mail=u'bcc@example.com', type=Recipient.TYPES.BCC)
        result = self._run_mail_cron_job()
        self.assertEqual(result[0].headers[u'To'], [u''])
        self.assertNotIn(u'Bcc Recipient', result[0].as_bytes)
        self.assertNotIn(u'bcc@example.com', result[0].as_bytes)

    def test_message_recipients_status_changed_to_sent(self):
        msg = self._create_message()
        to = self._create_recipient(message=msg, type=Recipient.TYPES.TO)
        cc = self._create_recipient(message=msg, type=Recipient.TYPES.CC)
        bcc = self._create_recipient(message=msg, type=Recipient.TYPES.BCC)
        result = self._run_mail_cron_job()
        to = Recipient.objects.get(pk=to.pk)
        cc = Recipient.objects.get(pk=cc.pk)
        bcc = Recipient.objects.get(pk=bcc.pk)
        self.assertEqual(to.status, Recipient.STATUSES.SENT)
        self.assertEqual(cc.status, Recipient.STATUSES.SENT)
        self.assertEqual(bcc.status, Recipient.STATUSES.SENT)
