# vim: expandtab
# -*- coding: utf-8 -*-
from django.test import TestCase

from . import CronTestCaseMixin
from ..test import mock_cron_jobs

class MockCronJobsTest(CronTestCaseMixin, TestCase):
    u"""
    Tests ``mock_cron_jobs()`` context manager.
    """

    def test_mock_cron_jobs_are_not_executed(self):
        u"""
        Checks that cron jobs run within ``mock_cron_jobs()`` context are logged as usual
        but they are not executed.
        """
        self._call_runcrons(
                run_every_mins=60,
                expected_call_count=0,
                expected_logs=[(True, None)],
                additional_context_managers=[mock_cron_jobs()],
                )
