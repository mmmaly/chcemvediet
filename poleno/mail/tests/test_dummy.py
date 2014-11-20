# vim: expandtab
# -*- coding: utf-8 -*-
from django.test import TestCase

from poleno.utils.misc import collect_stdout
from poleno.utils.test import override_signals, created_instances

from . import MailTestCaseMixin
from ..models import Message
from ..cron import mail as mail_cron_job
from ..signals import message_sent, message_received

class DummyTransportTest(MailTestCaseMixin, TestCase):
    u"""
    Tests ``DummyTransport`` mail transport class.
    """

    def _run_mail_cron_job(self):
        overrides = {
                u'EMAIL_OUTBOUND_TRANSPORT': u'poleno.mail.transports.dummy.DummyTransport',
                u'EMAIL_INBOUND_TRANSPORT': u'poleno.mail.transports.dummy.DummyTransport',
                }
        with self.settings(**overrides):
            with override_signals(message_sent, message_received):
                with collect_stdout():
                    mail_cron_job().do()


    def test_inbound_transport_does_not_create_any_message(self):
        with created_instances(Message.objects) as msg_set:
            self._run_mail_cron_job()
        self.assertFalse(msg_set.exists())

    def test_inbound_transport_marks_prequeued_inbound_message_processed(self):
        msg = self._create_message(type=Message.TYPES.INBOUND, processed=None)
        self._run_mail_cron_job()
        msg = Message.objects.get(pk=msg.pk)
        self.assertIsNotNone(msg.processed)

    def test_outbout_transport_marks_queued_outbound_message_processed(self):
        msg = self._create_message(type=Message.TYPES.OUTBOUND, processed=None)
        self._run_mail_cron_job()
        msg = Message.objects.get(pk=msg.pk)
        self.assertIsNotNone(msg.processed)
