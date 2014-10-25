# vim: expandtab
# -*- coding: utf-8 -*-
import datetime
import mock
import contextlib
import warnings

from django.core.management import call_command
from django.test import TestCase
from django_cron import CronJobLog

from poleno.utils.date import utc_now

from .. import cron_job


# ``contextlib.nested()`` is deprecated, but there is no other syntax to pass a list of context
# managers to a ``with`` statement afaik.
warnings.filterwarnings(u'ignore',
        message=u'With-statements now directly support multiple context managers',
        category=DeprecationWarning,
        )


mock_cron_job = None

class CronTestCaseMixin(TestCase):

    def _call_runcrons(self, mock_logs=(), expected_call_count=0, expected_logs=[], additional_context_managers=[], **cron_kwargs):
        mock_call = mock.Mock()

        @cron_job(**cron_kwargs)
        def mock_cron_job():
            mock_call()

        created_logs = []
        for delta, is_success, ran_at_time in mock_logs:
            created_logs.append(CronJobLog.objects.create(
                    code=mock_cron_job.code,
                    start_time=(utc_now() + delta),
                    end_time=(utc_now() + delta),
                    is_success=is_success,
                    ran_at_time=ran_at_time,
                    ))

        with mock.patch(u'poleno.cron.tests.mock_cron_job', mock_cron_job):
            with self.settings(CRON_CLASSES=(u'poleno.cron.tests.mock_cron_job',)):
                with contextlib.nested(*additional_context_managers):
                    # ``runcrons`` command runs ``logging.debug()`` that somehow spoils stderr.
                    with mock.patch(u'django_cron.logging'):
                        call_command(u'runcrons')

        self.assertEqual(mock_call.call_count, expected_call_count)

        found_logs = []
        for log in CronJobLog.objects.order_by(u'pk'):
            if log in created_logs:
                continue
            self.assertEqual(log.code, mock_cron_job.code)
            self.assertAlmostEqual(log.start_time, utc_now(), delta=datetime.timedelta(seconds=10))
            self.assertAlmostEqual(log.end_time, utc_now(), delta=datetime.timedelta(seconds=10))
            found_logs.append((log.is_success, log.ran_at_time))
        self.assertEqual(found_logs, expected_logs)
