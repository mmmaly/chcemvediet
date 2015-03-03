# vim: expandtab
# -*- coding: utf-8 -*-
import datetime

from django.test import TestCase
from django_cron import CronJobBase, CronJobLog

from poleno.timewarp import timewarp
from poleno.utils.date import local_datetime_from_local, utc_now

from . import CronTestCaseMixin
from .. import cron_job
from ..cron import clear_old_cronlogs

class CronJobTest(CronTestCaseMixin, TestCase):
    u"""
    Tests ``@cron_job`` decorator and ``runcrons`` behaviour when it runs and when it does not run
    registered cron jobs.
    """

    def test_decorator_with_run_every_mins(self):
        u"""
        Checks that ``@cron_job`` decorator registers the cron job correctly.
        """
        @cron_job(run_every_mins=60)
        def mock_cron_job():
            pass

        self.assertTrue(issubclass(mock_cron_job, CronJobBase))
        self.assertEqual(mock_cron_job.code, u'tests.mock_cron_job')
        self.assertEqual(mock_cron_job.__name__, u'mock_cron_job')
        self.assertEqual(mock_cron_job.schedule.run_every_mins, 60)
        self.assertEqual(mock_cron_job.schedule.run_at_times, [])
        self.assertEqual(mock_cron_job.schedule.retry_after_failure_mins, None)

    def test_decorator_with_run_every_mins_and_retry_after_failure_mins(self):
        u"""
        Checks that ``@cron_job`` decorator registers the cron job correctly.
        """
        @cron_job(run_every_mins=60, retry_after_failure_mins=5)
        def mock_cron_job():
            pass

        self.assertTrue(issubclass(mock_cron_job, CronJobBase))
        self.assertEqual(mock_cron_job.code, u'tests.mock_cron_job')
        self.assertEqual(mock_cron_job.__name__, u'mock_cron_job')
        self.assertEqual(mock_cron_job.schedule.run_every_mins, 60)
        self.assertEqual(mock_cron_job.schedule.run_at_times, [])
        self.assertEqual(mock_cron_job.schedule.retry_after_failure_mins, 5)

    def test_decorator_with_run_at_times(self):
        u"""
        Checks that ``@cron_job`` decorator registers the cron job correctly.
        """
        @cron_job(run_at_times=[u'10:30'])
        def mock_cron_job():
            pass

        self.assertTrue(issubclass(mock_cron_job, CronJobBase))
        self.assertEqual(mock_cron_job.code, u'tests.mock_cron_job')
        self.assertEqual(mock_cron_job.__name__, u'mock_cron_job')
        self.assertEqual(mock_cron_job.schedule.run_every_mins, None)
        self.assertEqual(mock_cron_job.schedule.run_at_times, [u'10:30'])
        self.assertEqual(mock_cron_job.schedule.retry_after_failure_mins, None)


    def test_run_every_mins_with_empty_logs(self):
        u"""
        Checks that the cron job is run if it's never been run yet.
        """
        self._call_runcrons(
                run_every_mins=60,
                expected_call_count=1,
                expected_logs=[(True, None)],
                )

    def test_run_every_mins_with_recent_successfull_run(self):
        u"""
        Checks that the cron job is not run if it was successfull less than ``run_every_mins`` ago.
        """
        self._call_runcrons(
                run_every_mins=60,
                mock_logs=[
                    (datetime.timedelta(minutes=-50), True, None),
                    ],
                expected_call_count=0,
                expected_logs=[],
                )

    def test_run_every_mins_with_old_successfull_run(self):
        u"""
        Checks that the cron job is run if it was successfull more than ``run_every_mins`` ago.
        """
        self._call_runcrons(
                run_every_mins=60,
                mock_logs=[
                    (datetime.timedelta(minutes=-70), True, None),
                    ],
                expected_call_count=1,
                expected_logs=[(True, None)],
                )

    def test_run_every_mins_with_recent_failed_run(self):
        u"""
        Checks that the cron job is run again if it failed its last run regardless of how long ago.

        If ``retry_after_failure_mins`` is ``None`` and the cron job fails, the job is run again
        and again until it's successfull. If it's never successfull, it's being run forever. It's
        a bit strange behaviour and looks like a design flaw in ``django_cron``. We should never
        use ``run_every_mins`` without high enough ``retry_after_failure_mins``.
        """
        self._call_runcrons(
                run_every_mins=60,
                mock_logs=[
                    (datetime.timedelta(minutes=-m), False, None) for m in range(100, 0, -1)
                    ],
                expected_call_count=1,
                expected_logs=[(True, None)],
                )

    def test_run_every_mins_with_recent_failed_run_with_retry_after_failure_mins(self):
        u"""
        Checks that the cron job is not run again if it failed less than
        ``retry_after_failure_mins`` ago.
        """
        self._call_runcrons(
                run_every_mins=60, retry_after_failure_mins=10,
                mock_logs=[
                    (datetime.timedelta(minutes=-m), False, None) for m in range(100, 0, -1)
                    ],
                expected_call_count=0,
                expected_logs=[],
                )

    def test_run_every_mins_with_old_failed_run_with_retry_after_failure_mins(self):
        u"""
        Checks that the cron job is run again if it failed more than ``retry_after_failure_mins``
        ago.
        """
        self._call_runcrons(
                run_every_mins=60, retry_after_failure_mins=10,
                mock_logs=[
                    (datetime.timedelta(minutes=-m-10), False, None) for m in range(100, 0, -1)
                    ],
                expected_call_count=1,
                expected_logs=[(True, None)],
                )

    def test_run_at_times_with_empty_logs_before_the_time(self):
        u"""
        Checks that the cron job is not run if it's less o'clock than ``run_at_times``, even if it
        was never run before.
        """
        timewarp.enable()
        timewarp.jump(local_datetime_from_local(2014, 10, 5, 9, 30, 0))
        self._call_runcrons(
                run_at_times=[u'10:00'],
                expected_call_count=0,
                expected_logs=[],
                )
        timewarp.reset()

    def test_run_at_times_with_empty_logs_after_the_time(self):
        u"""
        Checks that the cron job is run if it's more o'clock than ``run_at_times`` and it was never
        run before.
        """
        timewarp.enable()
        timewarp.jump(local_datetime_from_local(2014, 10, 5, 10, 30, 0))
        self._call_runcrons(
                run_at_times=[u'10:00'],
                expected_call_count=1,
                expected_logs=[(True, datetime.time(10, 0))],
                )
        timewarp.reset()

    def test_run_at_times_with_yesterday_successfull_run_before_the_time(self):
        u"""
        Checks that the cron job is not run if it's less o'clock than ``run_at_times`` and its last
        run was yesterday and was successfull.
        """
        timewarp.enable()
        timewarp.jump(local_datetime_from_local(2014, 10, 5, 9, 30, 0))
        self._call_runcrons(
                run_at_times=[u'10:00'],
                mock_logs=[
                    (datetime.timedelta(days=-1, hours=+1), True, datetime.time(10, 0)),
                    ],
                expected_call_count=0,
                expected_logs=[],
                )
        timewarp.reset()

    def test_run_at_times_with_yesterday_successfull_run_after_the_time(self):
        u"""
        Checks that the cron job is run if it's more o'clock than ``run_at_times`` and its last run
        was yesterday and was successfull.
        """
        timewarp.enable()
        timewarp.jump(local_datetime_from_local(2014, 10, 5, 10, 30, 0))
        self._call_runcrons(
                run_at_times=[u'10:00'],
                mock_logs=[
                    (datetime.timedelta(days=-1), True, datetime.time(10, 0)),
                    ],
                expected_call_count=1,
                expected_logs=[(True, datetime.time(10, 0))],
                )
        timewarp.reset()

    def test_run_at_times_with_today_successfull_run_before_the_time(self):
        u"""
        Checks that the cron job is not run if it's less o'clock than ``run_at_times`` and its last
        run was already today and was successfull.
        """
        timewarp.enable()
        timewarp.jump(local_datetime_from_local(2014, 10, 5, 9, 30, 0))
        self._call_runcrons(
                run_at_times=[u'10:00'],
                mock_logs=[
                    (datetime.timedelta(hours=-1), True, datetime.time(10, 0)),
                    ],
                expected_call_count=0,
                expected_logs=[],
                )
        timewarp.reset()

    def test_run_at_times_with_today_successfull_run_after_the_time(self):
        u"""
        Checks that the cron job is not run if it's more o'clock than ``run_at_times`` and its last
        run was already today and was successfull.
        """
        timewarp.enable()
        timewarp.jump(local_datetime_from_local(2014, 10, 5, 10, 30, 0))
        self._call_runcrons(
                run_at_times=[u'10:00'],
                mock_logs=[
                    (datetime.timedelta(hours=-2), True, datetime.time(10, 0)),
                    ],
                expected_call_count=0,
                expected_logs=[],
                )
        timewarp.reset()

    def test_run_at_multiple_times_with_today_successfull_run_before_the_time(self):
        u"""
        Checks that the cron job is not run if it's less o'clock than ``run_at_times[1]`` and its
        last run was already today for ``run_at_times[0]`` and was successfull.
        """
        timewarp.enable()
        timewarp.jump(local_datetime_from_local(2014, 10, 5, 12, 30, 0))
        self._call_runcrons(
                run_at_times=[u'10:00', u'13:00'],
                mock_logs=[
                    (datetime.timedelta(hours=-2), True, datetime.time(10, 0)),
                    ],
                expected_call_count=0,
                expected_logs=[],
                )
        timewarp.reset()

    def test_run_at_multiple_times_with_today_successfull_run_after_the_time(self):
        u"""
        Checks that the cron job is run if it's more o'clock than ``run_at_times[1]`` and its last
        run was already today for ``run_at_times[0]`` and was successfull.
        """
        timewarp.enable()
        timewarp.jump(local_datetime_from_local(2014, 10, 5, 13, 30, 0))
        self._call_runcrons(
                run_at_times=[u'10:00', u'13:00'],
                mock_logs=[
                    (datetime.timedelta(hours=-3), True, datetime.time(10, 0)),
                    ],
                expected_call_count=1,
                expected_logs=[(True, datetime.time(13, 0))],
                )
        timewarp.reset()

    def test_run_at_times_with_today_failed_run(self):
        u"""
        Checks that the cron job is NOT run even if it's more o'clock than ``run_at_times``
        plus ``retry_after_failure_mins`` and its last run was today, but failed.

        It's quite a strange behaviour, looks like a design flaw in ``django_cron``. I'd expect the
        job to be rerun after it fails.
        """
        timewarp.enable()
        timewarp.jump(local_datetime_from_local(2014, 10, 5, 11, 30, 0))
        self._call_runcrons(
                run_at_times=[u'10:00'], retry_after_failure_mins=30,
                mock_logs=[
                    (datetime.timedelta(hours=-1), False, datetime.time(10, 0)),
                    ],
                expected_call_count=0,
                expected_logs=[],
                )
        timewarp.reset()

class ClearOldCronlogsCronjobTest(TestCase):
    u"""
    Tests ``poleno.cron.cron.clear_old_cronlogs`` cron job.
    """

    def test_logs_older_that_one_week_are_cleared(self):
        old_log = CronJobLog.objects.create(
                code=u'mock_code',
                start_time=(utc_now() - datetime.timedelta(days=8)),
                end_time=(utc_now() - datetime.timedelta(days=8)),
                is_success=True,
                ran_at_time=None,
                )
        clear_old_cronlogs().do()
        self.assertFalse(CronJobLog.objects.filter(pk=old_log.pk).exists())

    def test_logs_newer_than_one_week_are_kept(self):
        old_log = CronJobLog.objects.create(
                code=u'mock_code',
                start_time=(utc_now() - datetime.timedelta(days=6)),
                end_time=(utc_now() - datetime.timedelta(days=6)),
                is_success=True,
                ran_at_time=None,
                )
        clear_old_cronlogs().do()
        self.assertTrue(CronJobLog.objects.filter(pk=old_log.pk).exists())
