# vim: expandtab
# -*- coding: utf-8 -*-
import datetime

from django.conf import settings
from django.utils import timezone

from poleno.cron import cron_job
from poleno.workdays import workdays
from poleno.utils.translation import translation

from models import Inforequest

@cron_job(run_at_times=[u'09:00'], retry_after_failure_mins=30)
def undecided_email_reminder():
    with translation(settings.LANGUAGE_CODE):
        for inforequest in Inforequest.objects.with_undecided_email():
            email = inforequest.newest_undecided_email
            last = inforequest.last_undecided_email_reminder
            if last and last > email.received_datetime:
                continue
            days = workdays.between(email.received_date, datetime.date.today())
            if days < 5:
                continue

            inforequest.send_undecided_email_reminder()

@cron_job(run_at_times=[u'09:00'], retry_after_failure_mins=30)
def obligee_deadline_reminder():
    with translation(settings.LANGUAGE_CODE):
        for inforequest in Inforequest.objects.without_undecided_email():
            for history in inforequest.history_set.all():
                if not history.last_action.has_obligee_deadline:
                    continue
                if not history.last_action.deadline_missed:
                    continue

                # The last reminder was sent after the deadline was extended for the last time iff
                # the extended deadline was missed before the reminder was sent. We don't want to
                # send any more reminders if the last reminder was sent after the deadline was
                # extended for the last time.
                last = history.last_action.last_deadline_reminder
                last_date = timezone.localtime(last).date() if last else None
                if last and history.last_action.deadline_missed_at(last_date):
                    continue

                inforequest.send_obligee_deadline_reminder(history.last_action)

@cron_job(run_at_times=[u'09:00'], retry_after_failure_mins=30)
def applicant_deadline_reminder():
    with translation(settings.LANGUAGE_CODE):
        for inforequest in Inforequest.objects.without_undecided_email():
            for history in inforequest.history_set.all():
                if not history.last_action.has_applicant_deadline:
                    continue

                # The reminder is sent 2 WDs before the deadline is missed.
                if history.last_action.deadline_remaining > 2:
                    continue

                # Applicant deadlines may not be extended, so we send at most one applicant
                # deadline reminder for the action.
                if history.last_action.last_deadline_reminder:
                    continue

                inforequest.send_applicant_deadline_reminder(history.last_action)
