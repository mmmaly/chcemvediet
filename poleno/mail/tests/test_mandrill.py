# vim: expandtab
# -*- coding: utf-8 -*-
import json
import mock
import contextlib

from django.core.urlresolvers import reverse
from django.core.exceptions import ImproperlyConfigured
from django.conf import settings
from django.http import HttpResponse, HttpResponseNotAllowed, HttpResponseForbidden, HttpResponseBadRequest
from django.test import TestCase

from poleno.utils.misc import Bunch, collect_stdout
from poleno.utils.test import override_signals, SecureClient

from . import MailTestCaseMixin
from ..models import Message, Recipient
from ..cron import mail as mail_cron_job
from ..signals import message_sent, message_received
from ..transports.mandrill.signals import webhook_event

class MandrillTransportTest(MailTestCaseMixin, TestCase):
    u"""
    Tests ``MandrillTransport`` mail transport class.
    """

    def _create_message(self, **kwargs):
        kwargs.setdefault(u'type', Message.TYPES.OUTBOUND)
        kwargs.setdefault(u'processed', None)
        return super(MandrillTransportTest, self)._create_message(**kwargs)

    def _create_recipient(self, **kwargs):
        kwargs.setdefault(u'status', Recipient.STATUSES.QUEUED)
        return super(MandrillTransportTest, self)._create_recipient(**kwargs)

    def _create_response(self, recipient, **kwargs):
        defaults = {
                u'email': recipient.mail,
                u'_id': u'remote-%s' % recipient.pk,
                u'status': u'sent',
                u'reject_reason': u'',
                }
        defaults.update(kwargs)
        return defaults

    def _run_mail_cron_job(self, status_code=200, response={}, delete_settings=(), **override_settings):
        overrides = {
                u'EMAIL_OUTBOUND_TRANSPORT': u'poleno.mail.transports.mandrill.MandrillTransport',
                u'EMAIL_INBOUND_TRANSPORT': None,
                u'MANDRILL_API_KEY': u'default_testing_api_key',
                u'MANDRILL_API_URL': u'https://defaulttestinghost/api'
                }
        overrides.update(override_settings)

        requests = mock.Mock()
        requests.post.return_value.status_code = status_code
        requests.post.return_value.text = u'Response text'
        requests.post.return_value.json.return_value = response

        with self.settings(**overrides):
            for name in delete_settings:
                delattr(settings, name)
            with mock.patch(u'poleno.mail.transports.mandrill.transport.requests', requests):
                with override_signals(message_sent, message_received):
                    with collect_stdout():
                        mail_cron_job().do()

        posts = [Bunch(url=call[0][0], data=json.loads(call[1][u'data'])) for call in requests.post.call_args_list]
        return posts


    def test_one_post_request_sent_for_every_message(self):
        msgs = [self._create_message() for i in range(10)]
        rcpts = [self._create_recipient(message=m) for m in msgs for i in range(3)]
        requests = self._run_mail_cron_job()
        self.assertEqual(len(requests), 10)

    def test_failed_post_request_raises_exception(self):
        msg = self._create_message()
        rcpt = self._create_recipient(message=msg)
        with self.assertRaisesMessage(RuntimeError, u'Sending Message(pk=%s) failed with status code 404. Mandrill response: Response text' % msg.pk):
            requests = self._run_mail_cron_job(status_code=404)

    def test_mandrill_api_key_setting(self):
        msg = self._create_message()
        rcpt = self._create_recipient(message=msg)
        requests = self._run_mail_cron_job(MANDRILL_API_KEY=u'test_api_key')
        self.assertEqual(requests[0].data[u'key'], u'test_api_key')

    def test_mandrill_api_key_setting_raises_exception_if_not_configured(self):
        msg = self._create_message()
        rcpt = self._create_recipient(message=msg)
        with self.assertRaisesMessage(ImproperlyConfigured, u'Setting MANDRILL_API_KEY is not set.'):
            requests = self._run_mail_cron_job(delete_settings=[u'MANDRILL_API_KEY'])

    def test_mandrill_api_url_setting(self):
        msg = self._create_message()
        rcpt = self._create_recipient(message=msg)
        requests = self._run_mail_cron_job(MANDRILL_API_URL=u'https://testhost/api/')
        self.assertEqual(requests[0].url, u'https://testhost/api/messages/send.json')

    def test_mandrill_api_url_setting_with_default_value_if_not_configured(self):
        msg = self._create_message()
        rcpt = self._create_recipient(message=msg)
        requests = self._run_mail_cron_job(delete_settings=[u'MANDRILL_API_URL'])
        self.assertEqual(requests[0].url, u'https://mandrillapp.com/api/1.0/messages/send.json')

    def test_message_subject(self):
        msg = self._create_message(subject=u'Testing subject')
        rcpt = self._create_recipient(message=msg)
        requests = self._run_mail_cron_job()
        self.assertEqual(requests[0].data[u'message'][u'subject'], u'Testing subject')

    def test_message_with_mising_subject(self):
        msg = self._create_message(omit=[u'subject'])
        rcpt = self._create_recipient(message=msg)
        requests = self._run_mail_cron_job()
        self.assertEqual(requests[0].data[u'message'][u'subject'], u'')

    def test_message_from_name_and_from_mail(self):
        msg = self._create_message(from_name=u'Agent Smith', from_mail=u'smith@example.com')
        rcpt = self._create_recipient(message=msg)
        requests = self._run_mail_cron_job()
        self.assertEqual(requests[0].data[u'message'][u'from_name'], u'Agent Smith')
        self.assertEqual(requests[0].data[u'message'][u'from_email'], u'smith@example.com')

    def test_message_with_comma_and_quotes_in_from_name(self):
        msg = self._create_message(from_name=u'Smith, "Agent"', from_mail=u'smith@example.com')
        rcpt = self._create_recipient(message=msg)
        requests = self._run_mail_cron_job()
        self.assertEqual(requests[0].data[u'message'][u'from_name'], u'Smith, "Agent"')
        self.assertEqual(requests[0].data[u'message'][u'from_email'], u'smith@example.com')

    def test_message_with_missing_from_name(self):
        msg = self._create_message(from_mail=u'smith@example.com', omit=[u'from_name'])
        rcpt = self._create_recipient(message=msg)
        requests = self._run_mail_cron_job()
        self.assertNotIn(u'from_name', requests[0].data[u'message'])
        self.assertEqual(requests[0].data[u'message'][u'from_email'], u'smith@example.com')

    def test_message_with_missing_both_from_name_and_from_mail(self):
        msg = self._create_message(omit=[u'from_name', u'from_mail'])
        rcpt = self._create_recipient(message=msg)
        requests = self._run_mail_cron_job()
        self.assertNotIn(u'from_name', requests[0].data[u'message'])
        self.assertEqual(requests[0].data[u'message'][u'from_email'], u'')

    def test_message_with_text_body_only(self):
        msg = self._create_message(text=u'Text content', omit=[u'html'])
        rcpt = self._create_recipient(message=msg)
        requests = self._run_mail_cron_job()
        self.assertEqual(requests[0].data[u'message'][u'text'], u'Text content')
        self.assertNotIn(u'html', requests[0].data[u'message'])

    def test_message_with_html_body_only(self):
        msg = self._create_message(html=u'<p>HTML content</p>', omit=[u'text'])
        rcpt = self._create_recipient(message=msg)
        requests = self._run_mail_cron_job()
        self.assertNotIn(u'text', requests[0].data[u'message'])
        self.assertEqual(requests[0].data[u'message'][u'html'], u'<p>HTML content</p>')

    def test_message_with_both_text_and_html_body(self):
        msg = self._create_message(text=u'Text content', html=u'<p>HTML content</p>')
        rcpt = self._create_recipient(message=msg)
        requests = self._run_mail_cron_job()
        self.assertEqual(requests[0].data[u'message'][u'text'], u'Text content')
        self.assertEqual(requests[0].data[u'message'][u'html'], u'<p>HTML content</p>')

    def test_message_with_neither_text_nor_html_body(self):
        msg = self._create_message(omit=[u'text', u'html'])
        rcpt = self._create_recipient(message=msg)
        requests = self._run_mail_cron_job()
        self.assertNotIn(u'text', requests[0].data[u'message'])
        self.assertNotIn(u'html', requests[0].data[u'message'])

    def test_message_with_extra_headers(self):
        msg = self._create_message(headers={u'X-Something': u'Value', u'X-Something-Else': u'Another Value'})
        rcpt = self._create_recipient(message=msg)
        requests = self._run_mail_cron_job()
        self.assertEqual(requests[0].data[u'message'][u'headers'], {u'X-Something': u'Value', u'X-Something-Else': u'Another Value'})

    def test_message_without_extra_headers(self):
        msg = self._create_message(omit=[u'headers'])
        rcpt = self._create_recipient(message=msg)
        requests = self._run_mail_cron_job()
        self.assertNotIn(u'headers', requests[0].data[u'message'])

    def test_message_to_cc_and_bcc_recipients(self):
        msg = self._create_message()
        to1 = self._create_recipient(message=msg, mail=u'to1@a.com', type=Recipient.TYPES.TO, name=u'To1')
        to2 = self._create_recipient(message=msg, mail=u'to2@a.com', type=Recipient.TYPES.TO, omit=[u'name'])
        cc1 = self._create_recipient(message=msg, mail=u'cc1@a.com', type=Recipient.TYPES.CC, name=u'Cc1')
        cc2 = self._create_recipient(message=msg, mail=u'cc2@a.com', type=Recipient.TYPES.CC, omit=[u'name'])
        bcc1 = self._create_recipient(message=msg, mail=u'bcc1@a.com', type=Recipient.TYPES.BCC, name=u'Bcc1')
        bcc2 = self._create_recipient(message=msg, mail=u'bcc2@a.com', type=Recipient.TYPES.BCC, omit=[u'name'])
        requests = self._run_mail_cron_job()
        self.assertItemsEqual(requests[0].data[u'message'][u'to'], [
            {u'type': u'to', u'email': u'to1@a.com', u'name': u'To1'},
            {u'type': u'to', u'email': u'to2@a.com'},
            {u'type': u'cc', u'email': u'cc1@a.com', u'name': u'Cc1'},
            {u'type': u'cc', u'email': u'cc2@a.com'},
            {u'type': u'bcc', u'email': u'bcc1@a.com', u'name': u'Bcc1'},
            {u'type': u'bcc', u'email': u'bcc2@a.com'},
            ])

    def test_message_attachments(self):
        msg = self._create_message()
        rcpt = self._create_recipient(message=msg)
        attch1 = self._create_attachment(generic_object=msg, content=u'Text content', name=u'filename.txt', content_type=u'text/plain')
        attch2 = self._create_attachment(generic_object=msg, content=u'(attachment content)', name=u'filename.pdf', content_type=u'application/pdf')
        requests = self._run_mail_cron_job()
        self.assertEqual(requests[0].data[u'message'][u'attachments'], [
            {u'content': u'VGV4dCBjb250ZW50', u'type': u'text/plain', u'name': u'filename.txt'},
            {u'content': u'KGF0dGFjaG1lbnQgY29udGVudCk=', u'type': u'application/pdf', u'name': u'filename.pdf'},
            ])

    def test_response_id_saved_as_recipient_remote_id(self):
        msg = self._create_message()
        rcpt = self._create_recipient(message=msg, mail=u'rcpt@a.com')
        response = self._create_response(rcpt)
        requests = self._run_mail_cron_job(response=[response])
        rcpt = Recipient.objects.get(pk=rcpt.pk)
        self.assertEqual(rcpt.remote_id, u'remote-%s' % rcpt.pk)

    def test_response_status_sent_saved_as_recipient_status_sent(self):
        msg = self._create_message()
        rcpt = self._create_recipient(message=msg, mail=u'rcpt@a.com')
        response = self._create_response(rcpt, status=u'sent')
        requests = self._run_mail_cron_job(response=[response])
        rcpt = Recipient.objects.get(pk=rcpt.pk)
        self.assertEqual(rcpt.status, Recipient.STATUSES.SENT)

    def test_response_status_queued_saved_as_recipient_status_queued(self):
        msg = self._create_message()
        rcpt = self._create_recipient(message=msg, mail=u'rcpt@a.com')
        response = self._create_response(rcpt, status=u'queued')
        requests = self._run_mail_cron_job(response=[response])
        rcpt = Recipient.objects.get(pk=rcpt.pk)
        self.assertEqual(rcpt.status, Recipient.STATUSES.QUEUED)

    def test_response_status_scheduled_saved_as_recipient_status_queued(self):
        msg = self._create_message()
        rcpt = self._create_recipient(message=msg, mail=u'rcpt@a.com')
        response = self._create_response(rcpt, status=u'scheduled')
        requests = self._run_mail_cron_job(response=[response])
        rcpt = Recipient.objects.get(pk=rcpt.pk)
        self.assertEqual(rcpt.status, Recipient.STATUSES.QUEUED)

    def test_response_status_rejected_saved_as_recipient_status_rejected_with_reject_reason_as_status_details(self):
        msg = self._create_message()
        rcpt = self._create_recipient(message=msg, mail=u'rcpt@a.com')
        response = self._create_response(rcpt, status=u'rejected', reject_reason=u'Test reason')
        requests = self._run_mail_cron_job(response=[response])
        rcpt = Recipient.objects.get(pk=rcpt.pk)
        self.assertEqual(rcpt.status, Recipient.STATUSES.REJECTED)
        self.assertEqual(rcpt.status_details, u'Test reason')

    def test_response_status_invalid_saved_as_recipient_status_invalid(self):
        msg = self._create_message()
        rcpt = self._create_recipient(message=msg, mail=u'rcpt@a.com')
        response = self._create_response(rcpt, status=u'invalid')
        requests = self._run_mail_cron_job(response=[response])
        rcpt = Recipient.objects.get(pk=rcpt.pk)
        self.assertEqual(rcpt.status, Recipient.STATUSES.INVALID)

    def test_other_response_status_saved_as_recipient_status_undefined(self):
        msg = self._create_message()
        rcpt = self._create_recipient(message=msg, mail=u'rcpt@a.com')
        response = self._create_response(rcpt, status=u'other')
        requests = self._run_mail_cron_job(response=[response])
        rcpt = Recipient.objects.get(pk=rcpt.pk)
        self.assertEqual(rcpt.status, Recipient.STATUSES.UNDEFINED)

    def test_response_id_and_status_saved_with_multiple_recipients(self):
        msg = self._create_message()
        rcpts = [self._create_recipient(message=msg, mail=u'rcpt-%d@a.com' % i) for i in range(20)]
        statuses = [
                (u'sent', Recipient.STATUSES.SENT),
                (u'queued', Recipient.STATUSES.QUEUED),
                (u'scheduled', Recipient.STATUSES.QUEUED),
                (u'rejected', Recipient.STATUSES.REJECTED),
                (u'invalid', Recipient.STATUSES.INVALID),
                (u'other', Recipient.STATUSES.UNDEFINED),
                ]
        response = [self._create_response(r, status=statuses[i%len(statuses)][0]) for i, r in enumerate(rcpts)]
        requests = self._run_mail_cron_job(response=response)
        for i, rcpt in enumerate(rcpts):
            rcpt = Recipient.objects.get(pk=rcpt.pk)
            self.assertEqual(rcpt.remote_id, u'remote-%s' % rcpt.pk)
            self.assertEqual(rcpt.status, statuses[i%len(statuses)][1])

class WebhookViewTest(MailTestCaseMixin, TestCase):
    u"""
    Tests ``webhook()`` view.
    """

    client_class = SecureClient
    urls = u'poleno.mail.transports.mandrill.urls'

    @contextlib.contextmanager
    def _overrides(self, delete_settings=(), **override_settings):
        overrides = {
                u'MANDRILL_WEBHOOK_SECRET': u'default_testing_secret',
                u'MANDRILL_WEBHOOK_SECRET_NAME': u'default_testing_secret_name',
                u'MANDRILL_WEBHOOK_KEYS': [u'default_testing_api_key'],
                u'MANDRILL_WEBHOOK_URL': u'https://defaulttestinghost/',
                }
        overrides.update(override_settings)

        with self.settings(**overrides):
            for name in delete_settings:
                delattr(settings, name)
            with override_signals(webhook_event):
                yield

    def _webhook_url(self, secret_name=u'default_testing_secret_name', secret=u'default_testing_secret'):
        return u'%s?%s=%s' % (reverse(u'webhook'), secret_name, secret)

    def _check_response(self, response, klass=HttpResponse, status_code=200, content=None):
        self.assertEqual(type(response), klass)
        self.assertEqual(response.status_code, status_code)
        if content is not None:
            self.assertEqual(response.content, content)


    def test_get_method_not_allowed(self):
        with self._overrides():
            response = self.client.get(self._webhook_url(), secure=True)
        self._check_response(response, HttpResponseNotAllowed, 405)
        self.assertEqual(response[u'Allow'], u'HEAD, POST')

    def test_head_method_allowed(self):
        with self._overrides():
            response = self.client.head(self._webhook_url(), secure=True)
        self._check_response(response)

    def test_post_method_allowed_and_needs_signature(self):
        with self._overrides():
            response = self.client.post(self._webhook_url(), secure=True)
        self._check_response(response, HttpResponseForbidden, 403, u'X-Mandrill-Signature not set')

    def test_non_secure_requests_forbidden(self):
        with self._overrides():
            response = self.client.head(self._webhook_url(), secure=False)
        self._check_response(response, HttpResponseForbidden, 403)

    def test_undefined_webhook_secret_raises_exception(self):
        with self._overrides(delete_settings=[u'MANDRILL_WEBHOOK_SECRET']):
            with self.assertRaisesMessage(ImproperlyConfigured, u'Setting MANDRILL_WEBHOOK_SECRET is not set.'):
                self.client.head(self._webhook_url(), secure=True)

    def test_webhook_secret_with_custom_name_matches(self):
        with self._overrides(MANDRILL_WEBHOOK_SECRET_NAME=u'custom_name', MANDRILL_WEBHOOK_SECRET=u'value'):
            response = self.client.head(self._webhook_url(u'custom_name', u'value'), secure=True)
        self._check_response(response)

    def test_webhook_secret_with_default_name_matches(self):
        with self._overrides(MANDRILL_WEBHOOK_SECRET=u'value', delete_settings=[u'MANDRILL_WEBHOOK_SECRET_NAME']):
            response = self.client.head(self._webhook_url(u'secret', u'value'), secure=True)
        self._check_response(response)

    def test_webhook_secret_with_custom_name_does_not_match(self):
        with self._overrides(MANDRILL_WEBHOOK_SECRET_NAME=u'custom_name', MANDRILL_WEBHOOK_SECRET=u'value'):
            response = self.client.head(self._webhook_url(u'custom_name', u'wrong_value'), secure=True)
        self._check_response(response, HttpResponseForbidden, 403)

    def test_webhook_secret_with_default_name_does_not_match(self):
        with self._overrides(MANDRILL_WEBHOOK_SECRET=u'value', delete_settings=[u'MANDRILL_WEBHOOK_SECRET_NAME']):
            response = self.client.head(self._webhook_url(u'secret', u'wrong_value'), secure=True)
        self._check_response(response, HttpResponseForbidden, 403)

    def test_undefined_webhook_url_raises_exception_for_post_request(self):
        with self._overrides(delete_settings=[u'MANDRILL_WEBHOOK_URL']):
            with self.assertRaisesMessage(ImproperlyConfigured, u'Setting MANDRILL_WEBHOOK_URL is not set.'):
                response = self.client.post(self._webhook_url(), secure=True)

    def test_undefined_webhook_url_does_not_raise_exception_for_head_request(self):
        with self._overrides(delete_settings=[u'MANDRILL_WEBHOOK_URL']):
            response = self.client.head(self._webhook_url(), secure=True)
        self._check_response(response)

    def test_undefined_webhook_keys_raises_exception_for_post_request(self):
        with self._overrides(delete_settings=[u'MANDRILL_WEBHOOK_KEYS']):
            with self.assertRaisesMessage(ImproperlyConfigured, u'Setting MANDRILL_WEBHOOK_KEYS is not set.'):
                response = self.client.post(self._webhook_url(), secure=True)

    def test_undefined_webhook_keys_does_not_raise_exception_for_head_request(self):
        with self._overrides(delete_settings=[u'MANDRILL_WEBHOOK_KEYS']):
            response = self.client.head(self._webhook_url(), secure=True)
        self._check_response(response)

    def test_post_request_with_missing_signature_forbidden(self):
        with self._overrides():
            response = self.client.post(self._webhook_url(), secure=True)
        self._check_response(response, HttpResponseForbidden, 403, u'X-Mandrill-Signature not set')

    def test_post_request_with_invalid_signature_forbidden(self):
        with self._overrides():
            response = self.client.post(self._webhook_url(), secure=True, HTTP_X_MANDRILL_SIGNATURE=u'invalid')
        self._check_response(response, HttpResponseForbidden, 403, u'Signature does not match')

    def test_post_request_with_valid_signature(self):
        with self._overrides(MANDRILL_WEBHOOK_URL=u'https://testhost/', MANDRILL_WEBHOOK_KEYS=[u'testkey']):
            response = self.client.post(self._webhook_url(), secure=True,
                    data={u'mandrill_events': json.dumps([])},
                    HTTP_X_MANDRILL_SIGNATURE=u'mOvq6ELcRGPELc0BwAFZn/PLZQA=')
        self._check_response(response)

    def test_post_request_with_missing_data_returns_bad_request(self):
        with self._overrides(MANDRILL_WEBHOOK_URL=u'https://testhost/', MANDRILL_WEBHOOK_KEYS=[u'testkey']):
            response = self.client.post(self._webhook_url(), secure=True,
                    HTTP_X_MANDRILL_SIGNATURE=u'UkKakpnkvjXLMRLs1kVknNgKXpk=')
        self._check_response(response, HttpResponseBadRequest, 400, u'Request syntax error')

    def test_post_request_with_invalid_data_returns_bad_request(self):
        with self._overrides(MANDRILL_WEBHOOK_URL=u'https://testhost/', MANDRILL_WEBHOOK_KEYS=[u'testkey']):
            response = self.client.post(self._webhook_url(), secure=True,
                    data={u'mandrill_events': u'invalid'},
                    HTTP_X_MANDRILL_SIGNATURE=u'Cu4i92MszJnwAhrkRXirRhGBb1o=')
        self._check_response(response, HttpResponseBadRequest, 400, u'Request syntax error')

    def test_post_request_with_valid_data_emits_webhook_events(self):
        with self._overrides(MANDRILL_WEBHOOK_URL=u'https://testhost/', MANDRILL_WEBHOOK_KEYS=[u'testkey']):
            receiver = mock.Mock()
            webhook_event.connect(receiver)
            response = self.client.post(self._webhook_url(), secure=True,
                    data={u'mandrill_events': json.dumps([
                        {u'event': u'deferral', u'_id': u'remote-1'},
                        {u'event': u'soft_bounce', u'_id': u'remote-2'},
                        {u'event': u'click', u'_id': u'remote-3'},
                        ])},
                    HTTP_X_MANDRILL_SIGNATURE=u'e/e0y1qBZghx4pyHFFoRrtgqmWg=')
        self._check_response(response)
        self.assertItemsEqual(receiver.mock_calls, [
            mock.call(signal=webhook_event, data={u'_id': u'remote-1', u'event': u'deferral'}, event_type=u'deferral', sender=None),
            mock.call(signal=webhook_event, data={u'_id': u'remote-2', u'event': u'soft_bounce'}, event_type=u'soft_bounce', sender=None),
            mock.call(signal=webhook_event, data={u'_id': u'remote-3', u'event': u'click'}, event_type=u'click', sender=None),
            ])
