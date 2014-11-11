# vim: expandtab
# -*- coding: utf-8 -*-
from django.conf import settings

from poleno.cron import cron_job
from poleno.workdays import workdays
from poleno.utils.translation import translation
from poleno.utils.date import local_date, local_today

from .models import Inforequest

# All these jobs do all their work the first time they are run in a day. Any later runs in the same
# day should do nothing. However, we run them multiple times in a day in case something was broken
# at the morning and the jobs failed.
RUN_AT_TIMES = [u'09:00', u'10:00', u'11:00', u'12:00', u'13:00', u'14:00']

@cron_job(run_at_times=RUN_AT_TIMES)
def undecided_email_reminder():
    with translation(settings.LANGUAGE_CODE):
        for inforequest in Inforequest.objects.not_closed().with_undecided_email():
            email = inforequest.newest_undecided_email
            last = inforequest.last_undecided_email_reminder
            if last and last > email.processed:
                continue
            days = workdays.between(local_date(email.processed), local_today())
            if days < 5:
                continue

            print(u'Sending undecided email reminder: %s' % repr(inforequest))
            inforequest.send_undecided_email_reminder()

@cron_job(run_at_times=RUN_AT_TIMES)
def obligee_deadline_reminder():
    with translation(settings.LANGUAGE_CODE):
        for inforequest in Inforequest.objects.not_closed().without_undecided_email():
            for branch in inforequest.branch_set.all():
                if not branch.last_action.has_obligee_deadline:
                    continue
                if not branch.last_action.deadline_missed:
                    continue

                # The last reminder was sent after the deadline was extended for the last time iff
                # the extended deadline was missed before the reminder was sent. We don't want to
                # send any more reminders if the last reminder was sent after the deadline was
                # extended for the last time.
                last = branch.last_action.last_deadline_reminder
                last_date = local_date(last) if last else None
                if last and branch.last_action.deadline_missed_at(last_date):
                    continue

                print(u'Sending obligee deadline reminder: %s' % repr(branch.last_action))
                inforequest.send_obligee_deadline_reminder(branch.last_action)

@cron_job(run_at_times=RUN_AT_TIMES)
def applicant_deadline_reminder():
    with translation(settings.LANGUAGE_CODE):
        for inforequest in Inforequest.objects.not_closed().without_undecided_email():
            for branch in inforequest.branch_set.all():
                if not branch.last_action.has_applicant_deadline:
                    continue

                # The reminder is sent 2 WDs before the deadline is missed.
                if branch.last_action.deadline_remaining > 2:
                    continue

                # Applicant deadlines may not be extended, so we send at most one applicant
                # deadline reminder for the action.
                if branch.last_action.last_deadline_reminder:
                    continue

                print(u'Sending applicant deadline reminder: %s' % repr(branch.last_action))
                inforequest.send_applicant_deadline_reminder(branch.last_action)

@cron_job(run_at_times=RUN_AT_TIMES)
def close_inforequests():
    for inforequest in Inforequest.objects.not_closed():
        for branch in inforequest.branch_set.all():
            if branch.last_action.has_deadline and branch.last_action.deadline_remaining > -100:
                break
        else:
            # Every branch that has a deadline have been missed for at least 100 WD.
            for branch in inforequest.branch_set.all():
                branch.add_expiration_if_expired()

            print(u'Closing inforequest: %s' % repr(inforequest))
            inforequest.closed = True
            inforequest.save()
