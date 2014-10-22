# vim: expandtab
# -*- coding: utf-8 -*-
import datetime
import mock

from django.core.management import call_command
from django.test import TestCase
from django_cron import CronJobLog

from poleno.utils.date import utc_now

class CleancronlogsManagementTest(TestCase):
    u"""
    Tests ``cleancronlogs`` management command.
    """

    def test_cleancronlogs(self):
        u"""
        Checks that ``cleancronlogs`` cleans cron logs.
        """
        CronJobLog.objects.create(
                code=u'mock_code',
                start_time=utc_now(),
                end_time=utc_now(),
                is_success=True,
                ran_at_time=datetime.time(10, 0),
                )
        CronJobLog.objects.create(
                code=u'mock_code2',
                start_time=utc_now(),
                end_time=utc_now(),
                is_success=False,
                ran_at_time=None,
                )
        call_command(u'cleancronlogs')
        self.assertEqual(CronJobLog.objects.count(), 0)

class CronserverManagementTest(TestCase):
    u"""
    Tests ``cronserver`` management command.
    """

    def test_clearlogs(self):
        u"""
        Checks that ``cronserver`` clears all cron logs if called with ``--clearlogs`` option.
        """
        CronJobLog.objects.create(
                code=u'mock_code',
                start_time=utc_now(),
                end_time=utc_now(),
                is_success=True,
                ran_at_time=None,
                )
        self.assertEqual(CronJobLog.objects.count(), 1)

        with mock.patch(u'poleno.cron.management.commands.cronserver.time.sleep', side_effect=KeyboardInterrupt):
            with mock.patch(u'poleno.cron.management.commands.cronserver.call_command'):
                call_command(u'cronserver', clearlogs=True)
        self.assertEqual(CronJobLog.objects.count(), 0)

    def test_clear_logs_from_future(self):
        u"""
        Checks that ``cronserver`` clears any cron logs from the future before every run, but keeps
        all logs from the past.
        """
        def side_effect():
            past_log = CronJobLog.objects.create(
                    code=u'mock_code',
                    start_time=(utc_now() + datetime.timedelta(hours=-1)),
                    end_time=(utc_now() + datetime.timedelta(hours=-1)),
                    is_success=True,
                    ran_at_time=None,
                    )
            future_log = CronJobLog.objects.create(
                    code=u'mock_code',
                    start_time=(utc_now() + datetime.timedelta(hours=+1)),
                    end_time=(utc_now() + datetime.timedelta(hours=+1)),
                    is_success=True,
                    ran_at_time=None,
                    )
            self.assertItemsEqual(CronJobLog.objects.all(), [past_log, future_log])
            yield None
            self.assertItemsEqual(CronJobLog.objects.all(), [past_log])
            yield KeyboardInterrupt

        with mock.patch(u'poleno.cron.management.commands.cronserver.time.sleep', side_effect=side_effect()):
            with mock.patch(u'poleno.cron.management.commands.cronserver.call_command'):
                call_command(u'cronserver')

    def test_interval(self):
        u"""
        Checks that ``cronserver`` takes ``--interval`` option into account.
        """
        with mock.patch(u'poleno.cron.management.commands.cronserver.time.sleep', side_effect=KeyboardInterrupt) as mock_sleep:
            with mock.patch(u'poleno.cron.management.commands.cronserver.call_command'):
                call_command(u'cronserver', interval=100)
        self.assertEqual(mock_sleep.mock_calls, [mock.call(100)])

    def test_multiple_cycles(self):
        u"""
        Checks ``cronserver`` with multiple calls to ``runcrons`` before interrupting.
        """
        with mock.patch(u'poleno.cron.management.commands.cronserver.time.sleep', side_effect=[None]*10 + [KeyboardInterrupt]):
            with mock.patch(u'poleno.cron.management.commands.cronserver.call_command') as mock_call_command:
                call_command(u'cronserver')
        self.assertEqual(mock_call_command.mock_calls, [mock.call(u'runcrons')] * 11)
