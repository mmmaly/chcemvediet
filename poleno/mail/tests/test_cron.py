# vim: expandtab
# -*- coding: utf-8 -*-
import datetime
import mock

from django.core.management import call_command
from django.test import TestCase

from poleno.timewarp import timewarp
from poleno.cron.test import mock_cron_jobs
from poleno.utils.date import utc_now, local_datetime_from_local
from poleno.utils.test import override_signals, created_instances

from . import MailTestCaseMixin
from ..models import Message
from ..cron import mail as mail_cron_job
from ..signals import message_sent, message_received

class MailCronjobTest(MailTestCaseMixin, TestCase):
    u"""
    Tests ``poleno.mail.cron.mail`` cron job. Checks that the job is run once every minute and
    queued outbound and inbound messages are processed.
    """

    def _call_runcrons(self):
        # ``runcrons`` command runs ``logging.debug()`` that somehow spoils stderr.
        with mock.patch(u'django_cron.logging'):
            call_command(u'runcrons')

    def _run_mail_cron_job(self, outbound=False, inbound=False,
            send_message_method=mock.DEFAULT, message_sent_receiver=None,
            get_messages_method=mock.DEFAULT, message_received_receiver=None):
        u"""
        Mocks mail transport, overrides ``message_sent`` and ``message_received`` signals, calls
        ``mail`` cron job and eats any stdout prited by the called job.
        """
        transport = u'poleno.mail.transports.base.BaseTransport'
        outbound_transport = transport if outbound else None
        inbound_transport = transport if inbound else None
        with self.settings(EMAIL_OUTBOUND_TRANSPORT=outbound_transport, EMAIL_INBOUND_TRANSPORT=inbound_transport):
            with mock.patch.multiple(transport, send_message=send_message_method, get_messages=get_messages_method):
                with override_signals(message_sent, message_received):
                    if message_sent_receiver is not None:
                        message_sent.connect(message_sent_receiver)
                    if message_received_receiver is not None:
                        message_received.connect(message_received_receiver)
                    mail_cron_job().do()


    def test_job_is_run_with_empty_logs(self):
        with mock_cron_jobs() as mock_jobs:
            self._call_runcrons()
        self.assertEqual(mock_jobs[u'poleno.mail.cron.mail'].call_count, 1)

    def test_job_is_not_run_again_before_timeout(self):
        timewarp.enable()
        with mock_cron_jobs() as mock_jobs:
            timewarp.jump(date=local_datetime_from_local(u'2010-10-05 10:00:00'))
            self._call_runcrons()
            timewarp.jump(date=local_datetime_from_local(u'2010-10-05 10:00:50'))
            self._call_runcrons()
        self.assertEqual(mock_jobs[u'poleno.mail.cron.mail'].call_count, 1)
        timewarp.reset()

    def test_job_is_run_again_after_timeout(self):
        timewarp.enable()
        with mock_cron_jobs() as mock_jobs:
            timewarp.jump(date=local_datetime_from_local(u'2010-10-05 10:00:00'))
            self._call_runcrons()
            timewarp.jump(date=local_datetime_from_local(u'2010-10-05 10:01:10'))
            self._call_runcrons()
        self.assertEqual(mock_jobs[u'poleno.mail.cron.mail'].call_count, 2)
        timewarp.reset()


    def test_outbound_transport(self):
        u"""
        Checks that the registered transport is used to send the queued message, the sent message
        is marked as processed and ``message_sent`` signal is emmited for it.
        """
        msg = self._create_message(type=Message.TYPES.OUTBOUND, processed=None)
        method, receiver = mock.Mock(), mock.Mock()
        self._run_mail_cron_job(outbound=True, send_message_method=method, message_sent_receiver=receiver)
        msg = Message.objects.get(pk=msg.pk)
        self.assertAlmostEqual(msg.processed, utc_now(), delta=datetime.timedelta(seconds=10))
        self.assertItemsEqual(method.mock_calls, [mock.call(msg)])
        self.assertItemsEqual(receiver.mock_calls, [mock.call(message=msg, sender=None, signal=message_sent)])

    def test_outbound_transport_with_no_queued_messages(self):
        u"""
        Checks that no transport method is called and no ``message_sent`` signal is emmited if
        there are no queued messages.
        """
        method, receiver = mock.Mock(), mock.Mock()
        self._run_mail_cron_job(outbound=True, send_message_method=method, message_sent_receiver=receiver)
        self.assertItemsEqual(method.mock_calls, [])
        self.assertItemsEqual(receiver.mock_calls, [])

    def test_outbound_transport_sends_at_most_10_messages_in_one_batch(self):
        msgs = [self._create_message(type=Message.TYPES.OUTBOUND, processed=None) for i in range(20)]
        method, receiver = mock.Mock(), mock.Mock()
        self._run_mail_cron_job(outbound=True, send_message_method=method, message_sent_receiver=receiver)

        # We expect first 10 messages (sorted by their ``pk``) to be sent.
        msgs = Message.objects.filter(pk__in=sorted(m.pk for m in msgs)[:10])
        self.assertEqual(len(msgs), 10)
        for msg in msgs:
            self.assertAlmostEqual(msg.processed, utc_now(), delta=datetime.timedelta(seconds=10))
        self.assertItemsEqual(method.mock_calls, [mock.call(m) for m in msgs])
        self.assertItemsEqual(receiver.mock_calls, [mock.call(message=m, sender=None, signal=message_sent) for m in msgs])

    def test_outbound_transport_lefts_message_unprocessed_if_exception_raised_while_pocessing_it(self):
        msgs = [self._create_message(type=Message.TYPES.OUTBOUND, processed=None) for i in range(3)]

        with mock.patch(u'poleno.mail.cron.nop', side_effect=[None, Exception, None]):
            with mock.patch(u'poleno.mail.cron.cron_logger') as logger:
                self._run_mail_cron_job(outbound=True)
        self.assertItemsEqual(Message.objects.filter(pk__in=(m.pk for m in msgs)).processed(), [msgs[0], msgs[2]])
        self.assertEqual(len(logger.mock_calls), 3)
        self.assertRegexpMatches(logger.mock_calls[0][1][0], u'Sent email: <Message: %s>' % msgs[0].pk)
        self.assertRegexpMatches(logger.mock_calls[1][1][0], u'Seding email failed: <Message: %s>' % msgs[1].pk)
        self.assertRegexpMatches(logger.mock_calls[2][1][0], u'Sent email: <Message: %s>' % msgs[2].pk)

    def test_inbound_transport(self):
        u"""
        Checks that ``message_received`` signal is emmited for all messages returned by the
        transport ``get_messages`` method.
        """
        msgs = []
        def method(transport):
            for i in range(3):
                msg = self._create_message(type=Message.TYPES.INBOUND, processed=None)
                msgs.append(msg)
                yield msg

        receiver = mock.Mock()
        self._run_mail_cron_job(inbound=True, get_messages_method=method, message_received_receiver=receiver)
        self.assertItemsEqual(receiver.mock_calls, [mock.call(message=m, sender=None, signal=message_received) for m in msgs])

    def test_inbound_transport_with_no_received_messages(self):
        def method(transport):
            return []

        receiver = mock.Mock()
        self._run_mail_cron_job(inbound=True, get_messages_method=method, message_received_receiver=receiver)
        self.assertItemsEqual(receiver.mock_calls, [])

    def test_inbound_transport_processes_at_most_10_messages_in_one_batch(self):
        msgs = []
        def method(transport):
            for i in range(20):
                msg = self._create_message(type=Message.TYPES.INBOUND, processed=None)
                msgs.append(msg)
                yield msg

        receiver = mock.Mock()
        self._run_mail_cron_job(inbound=True, get_messages_method=method, message_received_receiver=receiver)

        # We expect only first 10 messages (sorted by their ``pk``) to be processed.
        processed = Message.objects.filter(pk__in=sorted(m.pk for m in msgs)[:10])
        remaining = Message.objects.filter(pk__in=sorted(m.pk for m in msgs)[10:])
        self.assertEqual(len(processed), 10)
        self.assertEqual(len(remaining), 10)
        for msg in processed:
            self.assertAlmostEqual(msg.processed, utc_now(), delta=datetime.timedelta(seconds=10))
        for msg in remaining:
            self.assertIsNone(msg.processed)

    def test_inbound_transport_processes_prequeued_message(self):
        msg = self._create_message(type=Message.TYPES.INBOUND, processed=None)
        def method(transport):
            return []

        receiver = mock.Mock()
        self._run_mail_cron_job(inbound=True, get_messages_method=method, message_received_receiver=receiver)
        self.assertItemsEqual(receiver.mock_calls, [mock.call(message=msg, sender=None, signal=message_received)])

    def test_inbound_transport_stops_if_exception_raised_while_receiving_message(self):
        msgs = []
        def method(transport): # pragma: no cover
            for i in range(3):
                msg = self._create_message(type=Message.TYPES.INBOUND, processed=None)
                msgs.append(msg)
                yield msg

        with mock.patch(u'poleno.mail.cron.nop', side_effect=[None, Exception, None]):
            with mock.patch(u'poleno.mail.cron.cron_logger') as logger:
                with created_instances(Message.objects) as message_set:
                    self._run_mail_cron_job(inbound=True, get_messages_method=method)
        self.assertEqual(message_set.count(), 1)
        self.assertEqual(len(logger.mock_calls), 3)
        self.assertRegexpMatches(logger.mock_calls[0][1][0], u'Received email: <Message: %s>' % msgs[0].pk)
        self.assertRegexpMatches(logger.mock_calls[1][1][0], u'Receiving emails failed:')
        self.assertRegexpMatches(logger.mock_calls[2][1][0], u'Processed received email: <Message: %s>' % msgs[0].pk)

    def test_inbound_transport_lefts_message_unprocessed_if_exception_raised_while_pocessing_it(self):
        msgs = []
        def method(transport):
            for i in range(3):
                msg = self._create_message(type=Message.TYPES.INBOUND, processed=None)
                msgs.append(msg)
                yield msg

        with mock.patch(u'poleno.mail.cron.nop', side_effect=[None, None, None, None, Exception, None]):
            with mock.patch(u'poleno.mail.cron.cron_logger') as logger:
                with created_instances(Message.objects) as message_set:
                    self._run_mail_cron_job(inbound=True, get_messages_method=method)
        self.assertEqual(message_set.count(), 3)
        self.assertItemsEqual(message_set.processed(), [msgs[0], msgs[2]])
        self.assertEqual(len(logger.mock_calls), 6)
        self.assertRegexpMatches(logger.mock_calls[0][1][0], u'Received email: <Message: %s>' % msgs[0].pk)
        self.assertRegexpMatches(logger.mock_calls[1][1][0], u'Received email: <Message: %s>' % msgs[1].pk)
        self.assertRegexpMatches(logger.mock_calls[2][1][0], u'Received email: <Message: %s>' % msgs[2].pk)
        self.assertRegexpMatches(logger.mock_calls[3][1][0], u'Processed received email: <Message: %s>' % msgs[0].pk)
        self.assertRegexpMatches(logger.mock_calls[4][1][0], u'Processing received email failed: <Message: %s>' % msgs[1].pk)
        self.assertRegexpMatches(logger.mock_calls[5][1][0], u'Processed received email: <Message: %s>' % msgs[2].pk)
