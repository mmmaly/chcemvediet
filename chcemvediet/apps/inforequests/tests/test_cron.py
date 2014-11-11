# vim: expandtab
# -*- coding: utf-8 -*-
import mock
import datetime

from django.core.management import call_command
from django.test import TestCase

from poleno.mail.models import Message, Recipient
from poleno.timewarp import timewarp
from poleno.cron.test import mock_cron_jobs
from poleno.utils.date import local_datetime_from_local, utc_datetime_from_local
from poleno.utils.misc import collect_stdout
from poleno.utils.test import created_instances

from . import InforequestsTestCaseMixin
from ..cron import undecided_email_reminder, obligee_deadline_reminder, applicant_deadline_reminder, close_inforequests
from ..models import Inforequest, Action

class CronTestCaseMixin(TestCase):

    def _call_runcrons(self):
        # ``runcrons`` command runs ``logging.debug()`` that somehow spoils stderr.
        with mock.patch(u'django_cron.logging'):
            call_command(u'runcrons')

    def assert_times_job_is_run_at(self, cronjob):
        tests = (
                (u'07:10', False), (u'07:50', False), (u'08:10', False), (u'08:50', False),
                (u'09:10', True),  (u'09:50', False), (u'10:10', True),  (u'10:50', False),
                (u'11:10', True),  (u'11:50', False), (u'12:10', True),  (u'12:50', False),
                (u'13:10', True),  (u'13:50', False), (u'14:10', True),  (u'14:50', False),
                (u'15:10', False), (u'15:50', False), (u'16:10', False), (u'16:50', False),
                )

        for time, expected in tests:
            timewarp.jump(date=local_datetime_from_local(u'2010-10-05 %s' % time))
            with mock_cron_jobs() as mock_jobs:
                self._call_runcrons()
            if expected:
                self.assertEqual(mock_jobs[cronjob].call_count, 1, u'Cron job was not run at %s.' % time)
            else:
                self.assertEqual(mock_jobs[cronjob].call_count, 0, u'Cron job not run at %s.' % time)


class UndecidedEmailReminderCronJobTest(CronTestCaseMixin, InforequestsTestCaseMixin, TestCase):
    u"""
    Tests ``undecided_email_reminder()`` cron job.
    """

    def _call_cron_job(self):
        with mock.patch(u'chcemvediet.apps.inforequests.cron.workdays.between', side_effect=lambda a,b: (b-a).days):
            with created_instances(Message.objects) as message_set:
                with collect_stdout():
                    undecided_email_reminder().do()
        return message_set


    def test_times_job_is_run_at(self):
        self.assert_times_job_is_run_at(u'chcemvediet.apps.inforequests.cron.undecided_email_reminder')

    def test_undecided_email_reminder(self):
        timewarp.jump(local_datetime_from_local(u'2010-10-05 10:33:00'))
        user = self._create_user(email=u'smith@example.com')
        inforequest = self._create_inforequest(applicant=user)
        email = self._create_inforequest_email(inforequest=inforequest)

        timewarp.jump(local_datetime_from_local(u'2010-10-20 10:33:00'))
        with self.settings(DEFAULT_FROM_EMAIL=u'info@example.com'):
            with self.assertTemplateUsed(u'inforequests/mails/undecided_email_reminder_message.txt'):
                message_set = self._call_cron_job()
        msg = message_set.get()

        self.assertEqual(msg.from_formatted, u'info@example.com')
        self.assertEqual(msg.to_formatted, u'smith@example.com')

    def test_undecided_email_reminder_with_multiple_inforequests(self):
        timewarp.jump(local_datetime_from_local(u'2010-10-05 10:33:00'))
        inforequests = [self._create_inforequest() for i in range(5)]
        emails = [self._create_inforequest_email(inforequest=ir) for ir in inforequests]

        timewarp.jump(local_datetime_from_local(u'2010-10-20 10:33:00'))
        message_set = self._call_cron_job()
        self.assertEqual(message_set.count(), 5)

    def test_inforequest_last_undecided_email_reminder_is_updated_if_remider_is_sent(self):
        timewarp.jump(local_datetime_from_local(u'2010-10-05 10:33:00'))
        last = utc_datetime_from_local(u'2010-10-10 17:00:00')
        inforequest = self._create_inforequest(last_undecided_email_reminder=last)

        timewarp.jump(local_datetime_from_local(u'2010-10-10 18:00:00'))
        email = self._create_inforequest_email(inforequest=inforequest)

        timewarp.jump(local_datetime_from_local(u'2010-10-20 10:33:00'))
        message_set = self._call_cron_job()

        inforequest = Inforequest.objects.get(pk=inforequest.pk)
        self.assertAlmostEqual(inforequest.last_undecided_email_reminder, local_datetime_from_local(u'2010-10-20 10:33:00'), delta=datetime.timedelta(seconds=10))

    def test_inforequest_last_undecided_email_reminder_is_not_updated_if_reminder_is_not_sent(self):
        timewarp.jump(local_datetime_from_local(u'2010-10-05 10:33:00'))
        last = utc_datetime_from_local(u'2010-10-10 17:00:00')
        inforequest = self._create_inforequest(last_undecided_email_reminder=last)
        email = self._create_inforequest_email(inforequest=inforequest)

        timewarp.jump(local_datetime_from_local(u'2010-10-20 10:33:00'))
        message_set = self._call_cron_job()

        inforequest = Inforequest.objects.get(pk=inforequest.pk)
        self.assertEqual(inforequest.last_undecided_email_reminder, last)

    def test_reminder_is_not_sent_for_inforequest_without_undecided_email(self):
        timewarp.jump(local_datetime_from_local(u'2010-10-05 10:33:00'))
        inforequest = self._create_inforequest()

        timewarp.jump(local_datetime_from_local(u'2010-10-20 10:33:00'))
        message_set = self._call_cron_job()
        self.assertFalse(message_set.exists())

    def test_reminder_is_not_sent_for_closed_inforequest_with_undecided_email(self):
        timewarp.jump(local_datetime_from_local(u'2010-10-05 10:33:00'))
        inforequest = self._create_inforequest(closed=True)
        email = self._create_inforequest_email(inforequest=inforequest)

        timewarp.jump(local_datetime_from_local(u'2010-10-20 10:33:00'))
        message_set = self._call_cron_job()
        self.assertFalse(message_set.exists())

    def test_reminder_is_sent_for_not_closed_inforequest_with_undecided_email(self):
        timewarp.jump(local_datetime_from_local(u'2010-10-05 10:33:00'))
        inforequest = self._create_inforequest()
        email = self._create_inforequest_email(inforequest=inforequest)

        timewarp.jump(local_datetime_from_local(u'2010-10-20 10:33:00'))
        message_set = self._call_cron_job()
        self.assertTrue(message_set.exists())

    def test_reminder_is_not_sent_if_newest_undecided_email_is_not_at_least_5_days_old(self):
        timewarp.jump(local_datetime_from_local(u'2010-10-05 10:33:00'))
        inforequest = self._create_inforequest()
        email = self._create_inforequest_email(inforequest=inforequest)

        timewarp.jump(local_datetime_from_local(u'2010-10-16 10:33:00'))
        email = self._create_inforequest_email(inforequest=inforequest)

        timewarp.jump(local_datetime_from_local(u'2010-10-20 10:33:00'))
        message_set = self._call_cron_job()
        self.assertFalse(message_set.exists())

    def test_reminder_is_sent_if_newest_undecided_email_is_at_least_5_days_old(self):
        timewarp.jump(local_datetime_from_local(u'2010-10-05 10:33:00'))
        inforequest = self._create_inforequest()
        email = self._create_inforequest_email(inforequest=inforequest)

        timewarp.jump(local_datetime_from_local(u'2010-10-15 10:33:00'))
        email = self._create_inforequest_email(inforequest=inforequest)

        timewarp.jump(local_datetime_from_local(u'2010-10-20 10:33:00'))
        message_set = self._call_cron_job()
        self.assertTrue(message_set.exists())

    def test_reminder_is_not_sent_if_newest_undecided_email_older_than_last_reminder(self):
        timewarp.jump(local_datetime_from_local(u'2010-10-05 10:33:00'))
        last = utc_datetime_from_local(u'2010-10-10 17:00:00')
        inforequest = self._create_inforequest(last_undecided_email_reminder=last)
        email = self._create_inforequest_email(inforequest=inforequest)

        timewarp.jump(local_datetime_from_local(u'2010-10-10 13:00:00'))
        email = self._create_inforequest_email(inforequest=inforequest)

        timewarp.jump(local_datetime_from_local(u'2010-10-20 10:33:00'))
        message_set = self._call_cron_job()
        self.assertFalse(message_set.exists())

    def test_reminder_is_sent_if_newest_undecided_email_newer_than_last_reminder(self):
        timewarp.jump(local_datetime_from_local(u'2010-10-05 10:33:00'))
        last = utc_datetime_from_local(u'2010-10-10 17:00:00')
        inforequest = self._create_inforequest(last_undecided_email_reminder=last)
        email = self._create_inforequest_email(inforequest=inforequest)

        timewarp.jump(local_datetime_from_local(u'2010-10-10 18:00:00'))
        email = self._create_inforequest_email(inforequest=inforequest)

        timewarp.jump(local_datetime_from_local(u'2010-10-20 10:33:00'))
        message_set = self._call_cron_job()
        self.assertTrue(message_set.exists())

class ObligeeDeadlineReminderCronJobTest(CronTestCaseMixin, InforequestsTestCaseMixin, TestCase):
    u"""
    Tests ``obligee_deadline_reminder()`` cron job.
    """

    def _call_cron_job(self):
        with mock.patch(u'chcemvediet.apps.inforequests.cron.workdays.between', side_effect=lambda a,b: (b-a).days):
            with created_instances(Message.objects) as message_set:
                with collect_stdout():
                    obligee_deadline_reminder().do()
        return message_set


    def test_times_job_is_run_at(self):
        self.assert_times_job_is_run_at(u'chcemvediet.apps.inforequests.cron.obligee_deadline_reminder')

    def test_obligee_deadline_reminder(self):
        timewarp.jump(local_datetime_from_local(u'2010-10-05 10:33:00'))
        user = self._create_user(email=u'smith@example.com')
        inforequest, _, _ = self._create_inforequest_scenario(user)

        timewarp.jump(local_datetime_from_local(u'2010-11-20 10:33:00'))
        with self.settings(DEFAULT_FROM_EMAIL=u'info@example.com'):
            with self.assertTemplateUsed(u'inforequests/mails/obligee_deadline_reminder_message.txt'):
                message_set = self._call_cron_job()
        msg = message_set.get()

        self.assertEqual(msg.from_formatted, u'info@example.com')
        self.assertEqual(msg.to_formatted, u'smith@example.com')

    def test_obligee_deadline_reminder_with_multiple_inforequests(self):
        timewarp.jump(local_datetime_from_local(u'2010-10-05 10:33:00'))
        scenarios = [self._create_inforequest_scenario() for i in range(4)]

        timewarp.jump(local_datetime_from_local(u'2010-11-20 10:33:00'))
        message_set = self._call_cron_job()
        self.assertEqual(message_set.count(), 4)

    def test_obligee_deadline_reminder_with_inforequest_with_multiple_branches(self):
        timewarp.jump(local_datetime_from_local(u'2010-10-05 10:33:00'))
        inforequest, _, _ = self._create_inforequest_scenario((u'advancement', [], [], []))

        timewarp.jump(local_datetime_from_local(u'2010-11-20 10:33:00'))
        message_set = self._call_cron_job()
        self.assertEqual(message_set.count(), 3)

    def test_last_action_last_deadline_reminder_is_updated_if_remider_is_sent(self):
        timewarp.jump(local_datetime_from_local(u'2010-10-05 10:33:00'))
        last = utc_datetime_from_local(u'2010-10-10 17:00:00')
        inforequest, _, (request,) = self._create_inforequest_scenario((u'request', dict(last_deadline_reminder=last)))

        timewarp.jump(local_datetime_from_local(u'2010-11-20 10:33:00'))
        message_set = self._call_cron_job()

        request = Action.objects.get(pk=request.pk)
        self.assertAlmostEqual(request.last_deadline_reminder, local_datetime_from_local(u'2010-11-20 10:33:00'), delta=datetime.timedelta(seconds=10))

    def test_last_action_last_deadline_reminder_is_not_updated_if_remider_is_not_sent(self):
        timewarp.jump(local_datetime_from_local(u'2010-10-05 10:33:00'))
        last = utc_datetime_from_local(u'2010-11-10 17:00:00')
        inforequest, _, (request,) = self._create_inforequest_scenario((u'request', dict(last_deadline_reminder=last)))

        timewarp.jump(local_datetime_from_local(u'2010-11-20 10:33:00'))
        message_set = self._call_cron_job()

        request = Action.objects.get(pk=request.pk)
        self.assertEqual(request.last_deadline_reminder, last)

    def test_reminder_is_not_sent_for_inforequest_with_undecided_email(self):
        timewarp.jump(local_datetime_from_local(u'2010-10-05 10:33:00'))
        inforequest, _, _ = self._create_inforequest_scenario()
        email = self._create_inforequest_email(inforequest=inforequest)

        timewarp.jump(local_datetime_from_local(u'2010-11-20 10:33:00'))
        message_set = self._call_cron_job()
        self.assertFalse(message_set.exists())

    def test_reminder_is_not_sent_for_closed_inforequest_without_undecided_email(self):
        timewarp.jump(local_datetime_from_local(u'2010-10-05 10:33:00'))
        inforequest, _, _ = self._create_inforequest_scenario(dict(closed=True))

        timewarp.jump(local_datetime_from_local(u'2010-11-20 10:33:00'))
        message_set = self._call_cron_job()
        self.assertFalse(message_set.exists())

    def test_reminder_is_sent_for_not_closed_inforequest_without_undecided_email(self):
        timewarp.jump(local_datetime_from_local(u'2010-10-05 10:33:00'))
        inforequest, _, _ = self._create_inforequest_scenario()

        timewarp.jump(local_datetime_from_local(u'2010-11-20 10:33:00'))
        message_set = self._call_cron_job()
        self.assertTrue(message_set.exists())

    def test_reminder_is_not_sent_if_last_action_does_not_have_obligee_deadline(self):
        timewarp.jump(local_datetime_from_local(u'2010-10-05 10:33:00'))
        inforequest, _, _ = self._create_inforequest_scenario(u'clarification_request')

        timewarp.jump(local_datetime_from_local(u'2010-11-20 10:33:00'))
        message_set = self._call_cron_job()
        self.assertFalse(message_set.exists())

    def test_reminder_is_not_sent_if_last_action_deadline_is_not_missed(self):
        timewarp.jump(local_datetime_from_local(u'2010-10-05 10:33:00'))
        inforequest, _, _ = self._create_inforequest_scenario(
                u'clarification_request',
                # deadline is missed at 2010-10-11
                (u'clarification_response', dict(deadline=5)),
                )

        timewarp.jump(local_datetime_from_local(u'2010-10-10 10:33:00'))
        message_set = self._call_cron_job()
        self.assertFalse(message_set.exists())

    def test_reminder_is_sent_if_last_action_has_missed_obligee_deadline(self):
        timewarp.jump(local_datetime_from_local(u'2010-10-05 10:33:00'))
        inforequest, _, _ = self._create_inforequest_scenario(
                u'clarification_request',
                # deadline is missed at 2010-10-11
                (u'clarification_response', dict(deadline=5)),
                )

        timewarp.jump(local_datetime_from_local(u'2010-10-11 10:33:00'))
        message_set = self._call_cron_job()
        self.assertTrue(message_set.exists())

    def test_reminder_is_not_sent_if_last_action_deadline_was_already_missed_when_last_reminder_was_sent(self):
        timewarp.jump(local_datetime_from_local(u'2010-10-05 10:33:00'))
        last = utc_datetime_from_local(u'2010-10-11 10:33:00')
        inforequest, _, _ = self._create_inforequest_scenario(
                u'clarification_request',
                # deadline is missed at 2010-10-11
                (u'clarification_response', dict(deadline=5, last_deadline_reminder=last)),
                )

        timewarp.jump(local_datetime_from_local(u'2010-10-20 10:33:00'))
        message_set = self._call_cron_job()
        self.assertFalse(message_set.exists())

    def test_reminder_is_sent_if_last_action_deadline_was_not_missed_yet_when_last_reminder_was_sent(self):
        timewarp.jump(local_datetime_from_local(u'2010-10-05 10:33:00'))
        last = utc_datetime_from_local(u'2010-10-10 10:33:00')
        inforequest, _, _ = self._create_inforequest_scenario(
                u'clarification_request',
                # deadline is missed at 2010-10-11
                (u'clarification_response', dict(deadline=5, last_deadline_reminder=last)),
                )

        timewarp.jump(local_datetime_from_local(u'2010-10-20 10:33:00'))
        message_set = self._call_cron_job()
        self.assertTrue(message_set.exists())

    def test_reminder_is_sent_if_last_action_deadline_was_already_missed_when_last_reminder_was_sent_but_it_was_extended_later(self):
        timewarp.jump(local_datetime_from_local(u'2010-10-05 10:33:00'))
        last = utc_datetime_from_local(u'2010-10-12 10:33:00')
        inforequest, _, _ = self._create_inforequest_scenario(
                u'clarification_request',
                # deadline was missed at 2010-10-11, but then it was extended by 3 days; it will be
                # missed at 2010-10-14 again.
                (u'clarification_response', dict(deadline=5, extension=3, last_deadline_reminder=last)),
                )

        timewarp.jump(local_datetime_from_local(u'2010-10-20 10:33:00'))
        message_set = self._call_cron_job()
        self.assertTrue(message_set.exists())

class ApplicantDeadlineReminderCronJobTest(CronTestCaseMixin, InforequestsTestCaseMixin, TestCase):
    u"""
    Tests ``applicant_deadline_reminder()`` cron job.
    """

    def _call_cron_job(self):
        with mock.patch(u'chcemvediet.apps.inforequests.cron.workdays.between', side_effect=lambda a,b: (b-a).days):
            with created_instances(Message.objects) as message_set:
                with collect_stdout():
                    applicant_deadline_reminder().do()
        return message_set


    def test_times_job_is_run_at(self):
        self.assert_times_job_is_run_at(u'chcemvediet.apps.inforequests.cron.applicant_deadline_reminder')

    def test_applicant_deadline_reminder(self):
        timewarp.jump(local_datetime_from_local(u'2010-10-05 10:33:00'))
        user = self._create_user(email=u'smith@example.com')
        inforequest, _, _ = self._create_inforequest_scenario(user, u'clarification_request')

        timewarp.jump(local_datetime_from_local(u'2010-11-20 10:33:00'))
        with self.settings(DEFAULT_FROM_EMAIL=u'info@example.com'):
            with self.assertTemplateUsed(u'inforequests/mails/applicant_deadline_reminder_message.txt'):
                message_set = self._call_cron_job()
        msg = message_set.get()

        self.assertEqual(msg.from_formatted, u'info@example.com')
        self.assertEqual(msg.to_formatted, u'smith@example.com')

    def test_applicant_deadline_reminder_with_multiple_inforequests(self):
        timewarp.jump(local_datetime_from_local(u'2010-10-05 10:33:00'))
        scenarios = [self._create_inforequest_scenario(u'clarification_request') for i in range(4)]

        timewarp.jump(local_datetime_from_local(u'2010-11-20 10:33:00'))
        message_set = self._call_cron_job()
        self.assertEqual(message_set.count(), 4)

    def test_applicant_deadline_reminder_with_inforequest_with_multiple_branches(self):
        timewarp.jump(local_datetime_from_local(u'2010-10-05 10:33:00'))
        inforequest, _, _ = self._create_inforequest_scenario((u'advancement',
            [u'clarification_request'], [u'clarification_request'], [u'clarification_request']))

        timewarp.jump(local_datetime_from_local(u'2010-11-20 10:33:00'))
        message_set = self._call_cron_job()
        self.assertEqual(message_set.count(), 3)

    def test_last_action_last_deadline_reminder_is_updated_if_remider_is_sent(self):
        timewarp.jump(local_datetime_from_local(u'2010-10-05 10:33:00'))
        inforequest, _, (_, clarification_request) = self._create_inforequest_scenario(
                (u'clarification_request', dict(last_deadline_reminder=None)))

        timewarp.jump(local_datetime_from_local(u'2010-11-20 10:33:00'))
        message_set = self._call_cron_job()

        clarification_request = Action.objects.get(pk=clarification_request.pk)
        self.assertAlmostEqual(clarification_request.last_deadline_reminder, local_datetime_from_local(u'2010-11-20 10:33:00'), delta=datetime.timedelta(seconds=10))

    def test_last_action_last_deadline_reminder_is_not_updated_if_remider_is_not_sent(self):
        timewarp.jump(local_datetime_from_local(u'2010-10-05 10:33:00'))
        inforequest, _, (_, clarification_request) = self._create_inforequest_scenario(
                (u'clarification_request', dict(last_deadline_reminder=None)))

        timewarp.jump(local_datetime_from_local(u'2010-10-06 10:33:00'))
        message_set = self._call_cron_job()

        clarification_request = Action.objects.get(pk=clarification_request.pk)
        self.assertIsNone(clarification_request.last_deadline_reminder)

    def test_reminder_is_not_sent_for_inforequest_with_undecided_email(self):
        timewarp.jump(local_datetime_from_local(u'2010-10-05 10:33:00'))
        inforequest, _, _ = self._create_inforequest_scenario(u'clarification_request')
        email = self._create_inforequest_email(inforequest=inforequest)

        timewarp.jump(local_datetime_from_local(u'2010-11-20 10:33:00'))
        message_set = self._call_cron_job()
        self.assertFalse(message_set.exists())

    def test_reminder_is_not_sent_for_closed_inforequest_without_undecided_email(self):
        timewarp.jump(local_datetime_from_local(u'2010-10-05 10:33:00'))
        inforequest, _, _ = self._create_inforequest_scenario(dict(closed=True), u'clarification_request')

        timewarp.jump(local_datetime_from_local(u'2010-11-20 10:33:00'))
        message_set = self._call_cron_job()
        self.assertFalse(message_set.exists())

    def test_reminder_is_sent_for_not_closed_inforequest_without_undecided_email(self):
        timewarp.jump(local_datetime_from_local(u'2010-10-05 10:33:00'))
        inforequest, _, _ = self._create_inforequest_scenario(u'clarification_request')

        timewarp.jump(local_datetime_from_local(u'2010-11-20 10:33:00'))
        message_set = self._call_cron_job()
        self.assertTrue(message_set.exists())

    def test_reminder_is_not_sent_if_last_action_does_not_have_applicant_deadline(self):
        timewarp.jump(local_datetime_from_local(u'2010-10-05 10:33:00'))
        inforequest, _, _ = self._create_inforequest_scenario(u'clarification_request', u'clarification_response')

        timewarp.jump(local_datetime_from_local(u'2010-11-20 10:33:00'))
        message_set = self._call_cron_job()
        self.assertFalse(message_set.exists())

    def test_reminder_is_not_sent_if_last_action_deadline_will_be_missed_in_more_than_2_days(self):
        timewarp.jump(local_datetime_from_local(u'2010-10-05 10:33:00'))
        inforequest, _, _ = self._create_inforequest_scenario(
                # deadline is missed at 2010-10-11
                (u'clarification_request', dict(deadline=5)),
                )

        timewarp.jump(local_datetime_from_local(u'2010-10-07 10:33:00'))
        message_set = self._call_cron_job()
        self.assertFalse(message_set.exists())

    def test_reminder_is_sent_if_last_action_applicant_deadline_will_be_missed_in_2_days(self):
        timewarp.jump(local_datetime_from_local(u'2010-10-05 10:33:00'))
        inforequest, _, _ = self._create_inforequest_scenario(
                # deadline is missed at 2010-10-11
                (u'clarification_request', dict(deadline=5)),
                )

        timewarp.jump(local_datetime_from_local(u'2010-10-08 10:33:00'))
        message_set = self._call_cron_job()
        self.assertTrue(message_set.exists())

    def test_reminder_is_sent_if_last_action_applicant_deadline_is_already_missed(self):
        timewarp.jump(local_datetime_from_local(u'2010-10-05 10:33:00'))
        inforequest, _, _ = self._create_inforequest_scenario(
                # deadline is missed at 2010-10-11
                (u'clarification_request', dict(deadline=5)),
                )

        timewarp.jump(local_datetime_from_local(u'2010-10-11 10:33:00'))
        message_set = self._call_cron_job()
        self.assertTrue(message_set.exists())

    def test_reminder_is_not_sent_twice_for_one_action(self):
        timewarp.jump(local_datetime_from_local(u'2010-10-05 10:33:00'))
        last = utc_datetime_from_local(u'2010-10-11 10:33:00')
        inforequest, _, _ = self._create_inforequest_scenario((u'clarification_request', dict(last_deadline_reminder=last)))

        timewarp.jump(local_datetime_from_local(u'2010-11-20 10:33:00'))
        message_set = self._call_cron_job()
        self.assertFalse(message_set.exists())

    def test_reminder_is_sent_for_last_action_even_if_it_was_sent_for_previous_actions(self):
        timewarp.jump(local_datetime_from_local(u'2010-10-05 10:33:00'))
        last = utc_datetime_from_local(u'2010-10-11 10:33:00')
        inforequest, _, _ = self._create_inforequest_scenario(
                (u'clarification_request', dict(last_deadline_reminder=last)),
                u'clarification_response',
                (u'clarification_request', dict(last_deadline_reminder=None)),
                )

        timewarp.jump(local_datetime_from_local(u'2010-11-20 10:33:00'))
        message_set = self._call_cron_job()
        self.assertTrue(message_set.exists())

class CloseInforequestsCronJobTest(CronTestCaseMixin, InforequestsTestCaseMixin, TestCase):
    u"""
    Tests ``close_inforequests()`` cron job.
    """

    def _call_cron_job(self):
        with mock.patch(u'chcemvediet.apps.inforequests.cron.workdays.between', side_effect=lambda a,b: (b-a).days):
            with collect_stdout():
                close_inforequests().do()


    def test_times_job_is_run_at(self):
        self.assert_times_job_is_run_at(u'chcemvediet.apps.inforequests.cron.close_inforequests')

    def test_close_inforequests(self):
        timewarp.jump(local_datetime_from_local(u'2010-03-05 10:33:00'))
        inforequest, _, _ = self._create_inforequest_scenario()

        timewarp.jump(local_datetime_from_local(u'2010-10-05 10:33:00'))
        self._call_cron_job()

        inforequest = Inforequest.objects.get(pk=inforequest.pk)
        self.assertTrue(inforequest.closed)

    def test_close_inforequests_with_multiple_inforequests(self):
        timewarp.jump(local_datetime_from_local(u'2010-03-05 10:33:00'))
        scenarios = [self._create_inforequest_scenario() for i in range(5)]

        timewarp.jump(local_datetime_from_local(u'2010-10-05 10:33:00'))
        self._call_cron_job()

        for inforequest, _, _ in scenarios:
            inforequest = Inforequest.objects.get(pk=inforequest.pk)
            self.assertTrue(inforequest.closed)

    def test_expiration_added_if_last_action_has_obligee_deadline(self):
        timewarp.jump(local_datetime_from_local(u'2010-03-05 10:33:00'))
        _, branch, _ = self._create_inforequest_scenario()

        timewarp.jump(local_datetime_from_local(u'2010-10-05 10:33:00'))
        with created_instances(branch.action_set) as action_set:
            self._call_cron_job()
        action = action_set.get()

        self.assertEqual(action.type, Action.TYPES.EXPIRATION)

    def test_expiration_not_added_if_last_action_does_not_have_obligee_deadline(self):
        timewarp.jump(local_datetime_from_local(u'2010-03-05 10:33:00'))
        _, branch, _ = self._create_inforequest_scenario(u'disclosure')

        timewarp.jump(local_datetime_from_local(u'2010-10-05 10:33:00'))
        with created_instances(branch.action_set) as action_set:
            self._call_cron_job()
        self.assertFalse(action_set.exists())

    def test_expiration_not_added_if_inforequest_is_already_closed(self):
        timewarp.jump(local_datetime_from_local(u'2010-03-05 10:33:00'))
        _, branch, _ = self._create_inforequest_scenario(dict(closed=True))

        timewarp.jump(local_datetime_from_local(u'2010-10-05 10:33:00'))
        with created_instances(branch.action_set) as action_set:
            self._call_cron_job()
        self.assertFalse(action_set.exists())

    def test_expirations_added_for_inforequest_with_multiple_branches(self):
        timewarp.jump(local_datetime_from_local(u'2010-03-05 10:33:00'))
        _, branch, actions = self._create_inforequest_scenario((u'advancement',
                [u'confirmation'],
                [u'clarification_request'],
                [u'clarification_request', u'clarification_response'],
                ))
        _, (_, [(branch1, _), (branch2, _), (branch3, _)]) = actions

        timewarp.jump(local_datetime_from_local(u'2010-10-05 10:33:00'))
        with created_instances(branch.action_set) as action_set:
            with created_instances(branch1.action_set) as action_set1:
                with created_instances(branch2.action_set) as action_set2:
                    with created_instances(branch3.action_set) as action_set3:
                        self._call_cron_job()
        self.assertFalse(action_set.exists())
        self.assertTrue(action_set1.exists())
        self.assertFalse(action_set2.exists())
        self.assertTrue(action_set3.exists())

    def test_inforequest_is_not_closed_if_last_action_deadline_was_missed_less_than_100_days_ago(self):
        timewarp.jump(local_datetime_from_local(u'2010-03-01 10:33:00'))
        inforequest, _, _ = self._create_inforequest_scenario((u'request', dict(deadline=10)))

        # Request deadline was missed at 2010-03-11. 100 days after missing the deadline will pass
        # at 2010-06-19.
        timewarp.jump(local_datetime_from_local(u'2010-06-18 10:33:00'))
        self._call_cron_job()

        inforequest = Inforequest.objects.get(pk=inforequest.pk)
        self.assertFalse(inforequest.closed)

    def test_inforequest_is_closed_if_last_action_deadline_was_missed_at_least_100_days_ago(self):
        timewarp.jump(local_datetime_from_local(u'2010-03-01 10:33:00'))
        inforequest, _, _ = self._create_inforequest_scenario((u'request', dict(deadline=10)))

        # Request deadline was missed at 2010-03-11. 100 days after missing the deadline will pass
        # at 2010-06-19.
        timewarp.jump(local_datetime_from_local(u'2010-06-19 10:33:00'))
        self._call_cron_job()

        inforequest = Inforequest.objects.get(pk=inforequest.pk)
        self.assertTrue(inforequest.closed)

    def test_inforequest_is_closed_if_last_action_has_no_deadline(self):
        inforequest, _, _ = self._create_inforequest_scenario(u'refusal', u'appeal', u'affirmation')
        self._call_cron_job()

        inforequest = Inforequest.objects.get(pk=inforequest.pk)
        self.assertTrue(inforequest.closed)

    def test_inforequest_is_not_closed_if_at_least_one_branch_prevents_it(self):
        inforequest, _, _ = self._create_inforequest_scenario((u'advancement',
                [u'refusal', u'appeal', u'affirmation'],
                [(u'disclosure', dict(disclosure_level=Action.DISCLOSURE_LEVELS.PARTIAL))],
                [u'refusal', u'appeal', u'reversion'],
                ))
        self._call_cron_job()

        inforequest = Inforequest.objects.get(pk=inforequest.pk)
        self.assertFalse(inforequest.closed)

    def test_inforequest_is_closed_if_no_branch_prevents_it(self):
        inforequest, _, _ = self._create_inforequest_scenario((u'advancement',
                [u'refusal', u'appeal', u'affirmation'],
                [(u'disclosure', dict(disclosure_level=Action.DISCLOSURE_LEVELS.FULL))],
                [u'refusal', u'appeal', u'reversion'],
                ))
        self._call_cron_job()

        inforequest = Inforequest.objects.get(pk=inforequest.pk)
        self.assertTrue(inforequest.closed)
