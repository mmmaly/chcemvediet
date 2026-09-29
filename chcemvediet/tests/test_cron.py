# vim: expandtab
# -*- coding: utf-8 -*-
import datetime

from django.contrib.auth.models import User
from django.contrib.sessions.models import Session
from django.test import TestCase
from django_cron.models import CronJobLog

from poleno.mail.models import Message
from poleno.mail.tests import MailTestCaseMixin
from poleno.timewarp import timewarp
from poleno.utils.date import utc_datetime_from_local, utc_now
from poleno.utils.test import created_instances

from ..cron import clear_expired_sessions, send_daily_status


class ClearExpiredSessionsCronjobTest(TestCase):
    u"""
    Tests ``chcemvediet.cron.clear_expired_sessions`` cron job.
    """

    def _pre_setup(self):
        super(ClearExpiredSessionsCronjobTest, self)._pre_setup()
        timewarp.enable()
        timewarp.reset()

    def _post_teardown(self):
        timewarp.reset()
        super(ClearExpiredSessionsCronjobTest, self)._post_teardown()

    def test_sessions_older_than_two_weeks_are_cleared(self):
        timewarp.jump(utc_datetime_from_local(u'2014-10-01 09:30:00'))
        user = User.objects.create_user(u'aaa', password=u'ppp')
        self.client.login(username=user.username, password=u'ppp')

        timewarp.jump(utc_datetime_from_local(u'2014-10-16 09:30:00'))
        self.assertTrue(Session.objects.exists())
        clear_expired_sessions().do()
        self.assertFalse(Session.objects.exists())

    def test_sessions_newer_than_two_weeks_are_kept(self):
        timewarp.jump(utc_datetime_from_local(u'2014-10-01 09:30:00'))
        user = User.objects.create_user(u'aaa', password=u'ppp')
        self.client.login(username=user.username, password=u'ppp')

        timewarp.jump(utc_datetime_from_local(u'2014-10-14 09:30:00'))
        self.assertTrue(Session.objects.exists())
        clear_expired_sessions().do()
        self.assertTrue(Session.objects.exists())


class SendDailyStatusCronjobTest(MailTestCaseMixin, TestCase):
    u"""
    Tests ``chcemvediet.cron.send_daily_status`` cron job.
    """

    def _call_cron_job(self):
        with created_instances(Message.objects) as message_set:
            send_daily_status().do()
        return message_set

    def _create_message_created_at(self, created, **kwargs):
        msg = self._create_message(**kwargs)
        Message.objects.filter(pk=msg.pk).update(created=created)
        return msg


    def test_ok_status_is_sent_to_admins(self):
        self._create_message_created_at(utc_now() - datetime.timedelta(hours=2))
        message_set = self._call_cron_job()
        msg = message_set.get()
        self.assertEqual(msg.type, Message.TYPES.OUTBOUND)
        self.assertIsNone(msg.processed)
        self.assertTrue(msg.subject.endswith(u'Daily status: OK'))
        self.assertIn(u'No problems found.', msg.text)
        self.assertIn(u'Inbound received: 1', msg.text)
        self.assertEqual([r.mail for r in msg.recipients], [u'admin@example.com'])

    def test_status_is_sent_even_if_nothing_happened(self):
        message_set = self._call_cron_job()
        msg = message_set.get()
        self.assertTrue(msg.subject.endswith(u'Daily status: 1 problem(s)'))
        self.assertIn(u'no inbound message for more than 5 days', msg.text)

    def test_problems_are_reported(self):
        self._create_message_created_at(utc_now() - datetime.timedelta(hours=2))
        self._create_message_created_at(utc_now() - datetime.timedelta(hours=1),
                type=Message.TYPES.OUTBOUND, processed=None)
        self._create_message_created_at(utc_now() - datetime.timedelta(hours=1),
                processed=None)
        CronJobLog.objects.create(code=u'mail.mail', start_time=utc_now(), end_time=utc_now(),
                is_success=False)
        message_set = self._call_cron_job()
        msg = message_set.get()
        self.assertTrue(msg.subject.endswith(u'Daily status: 3 problem(s)'))
        self.assertIn(u'1 outbound messages waiting longer than 15 minutes', msg.text)
        self.assertIn(u'1 inbound messages unprocessed longer than 15 minutes', msg.text)
        self.assertIn(u'cron job mail.mail failed 1 times', msg.text)
