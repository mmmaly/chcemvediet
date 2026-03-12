# vim: expandtab
# -*- coding: utf-8 -*-
import traceback

from django.db import transaction
from django.conf import settings

from poleno.cron import cron_job, cron_logger
from poleno.workdays import workdays
from poleno.utils.translation import translation
from poleno.utils.date import local_date, local_today
from poleno.utils.misc import nop

from .constants import DAYS_TO_CLOSE_INFOREQUEST
from .models import Inforequest, Branch


@cron_job(run_at_times=settings.CRON_USER_INTERACTION_TIMES)
@transaction.atomic
def undecided_email_reminder():
    with translation(settings.LANGUAGE_CODE):
        inforequests = (Inforequest.objects
                .not_closed()
                .with_undecided_email()
                .prefetch_related(Inforequest.prefetch_newest_undecided_email())
                )

        filtered = []
        for inforequest in inforequests:
            try:
                email = inforequest.newest_undecided_email
                last = inforequest.last_undecided_email_reminder
                if last and last > email.processed:
                    continue
                days = workdays.between(local_date(email.processed), local_today())
                if days < 5:
                    continue
                nop()  # To let tests raise testing exception here.
                filtered.append(inforequest)
            except Exception:
                msg = u'Checking if undecided email reminder should be sent failed: {}\n{}'
                trace = traceback.format_exc()
                cron_logger.error(msg.format(inforequest, trace))

        if not filtered:
            return

        filtered = (Inforequest.objects
                .select_related(u'applicant')
                .select_undecided_emails_count()
                .prefetch_related(Inforequest.prefetch_main_branch(None,
                    Branch.objects.select_related(u'historicalobligee')))
                .prefetch_related(Inforequest.prefetch_newest_undecided_email())
                .filter(pk__in=(o.pk for o in filtered))
                )
        for inforequest in filtered:
            try:
                with transaction.atomic():
                    inforequest.send_undecided_email_reminder()
                    nop()  # To let tests raise testing exception here.
                    cron_logger.info(u'Sent undecided email reminder: {}'.format(inforequest))
            except Exception:
                msg = u'Sending undecided email reminder failed: {}\n{}'
                trace = traceback.format_exc()
                cron_logger.error(msg.format(inforequest, trace))

@cron_job(run_at_times=settings.CRON_USER_INTERACTION_TIMES)
@transaction.atomic
def obligee_deadline_reminder():
    with translation(settings.LANGUAGE_CODE):
        inforequests = (Inforequest.objects
                .not_closed()
                .without_undecided_email()
                .prefetch_related(Inforequest.prefetch_branches())
                .prefetch_related(Branch.prefetch_last_action(u'branches'))
                )

        filtered = []
        for inforequest in inforequests:
            for branch in inforequest.branches:
                action = branch.last_action
                try:
                    if not action.has_obligee_deadline_snooze_missed:
                        continue
                    # The last reminder was sent after the applicant snoozed for the last time iff
                    # the snooze was missed before the reminder was sent. We don't want to send any
                    # more reminders if the last reminder was sent after the last snooze.
                    last = action.last_deadline_reminder
                    last_date = local_date(last) if last else None
                    if last and action.deadline.is_snooze_missed_at(last_date):
                        continue
                    nop()  # To let tests raise testing exception here.
                    filtered.append(branch)
                except Exception:
                    msg = u'Checking if obligee deadline reminder should be sent failed: {}\n{}'
                    trace = traceback.format_exc()
                    cron_logger.error(msg.format(action, trace))

        if not filtered:
            return

        filtered = (Branch.objects
                .select_related(u'inforequest__applicant')
                .select_related(u'historicalobligee')
                .prefetch_related(Branch.prefetch_last_action())
                .filter(pk__in=(o.pk for o in filtered))
                )
        for branch in filtered:
            try:
                with transaction.atomic():
                    branch.inforequest.send_obligee_deadline_reminder(branch.last_action)
                    nop()  # To let tests raise testing exception here.
                    msg = u'Sent obligee deadline reminder: {}'
                    cron_logger.info(msg.format(branch.last_action))
            except Exception:
                msg = u'Sending obligee deadline reminder failed: {}\n{}'
                trace = traceback.format_exc()
                cron_logger.error(msg.format(branch.last_action, trace))

@cron_job(run_at_times=settings.CRON_USER_INTERACTION_TIMES)
@transaction.atomic
def applicant_deadline_reminder():
    with translation(settings.LANGUAGE_CODE):
        inforequests = (Inforequest.objects
                .not_closed()
                .without_undecided_email()
                .prefetch_related(Inforequest.prefetch_branches())
                .prefetch_related(Branch.prefetch_last_action(u'branches'))
                )

        filtered = []
        for inforequest in inforequests:
            for branch in inforequest.branches:
                action = branch.last_action
                try:
                    if not action.has_applicant_deadline:
                        continue
                    # The reminder is sent 2 CD before the deadline is missed.
                    if action.deadline.calendar_days_remaining > 2:
                        continue
                    # Applicant may not snooze his deadlines, so we send at most one applicant
                    # deadline reminder for the action.
                    if action.last_deadline_reminder:
                        continue
                    nop()  # To let tests raise testing exception here.
                    filtered.append(branch)
                except Exception:
                    msg = u'Checking if applicant deadline reminder should be sent failed: {}\n{}'
                    trace = traceback.format_exc()
                    cron_logger.error(msg.format(action, trace))

        if not filtered:
            return

        filtered = (Branch.objects
                .select_related(u'inforequest__applicant')
                .prefetch_related(Branch.prefetch_last_action())
                .filter(pk__in=(o.pk for o in filtered))
                )
        for branch in filtered:
            try:
                with transaction.atomic():
                    branch.inforequest.send_applicant_deadline_reminder(branch.last_action)
                    nop()  # To let tests raise testing exception here.
                    msg = u'Sent applicant deadline reminder: {}'
                    cron_logger.info(msg.format(branch.last_action))
            except Exception:
                msg = u'Sending applicant deadline reminder failed: {}\n{}'
                trace = traceback.format_exc()
                cron_logger.error(msg.format(branch.last_action, trace))

@cron_job(run_at_times=settings.CRON_IMPORTANT_MAINTENANCE_TIMES)
@transaction.atomic
def close_inforequests():
    inforequests = (Inforequest.objects
            .not_closed()
            .prefetch_related(Inforequest.prefetch_branches())
            .prefetch_related(Branch.prefetch_last_action(u'branches'))
            )

    filtered = []
    for inforequest in inforequests:
        try:
            for branch in inforequest.branches:
                action = branch.last_action
                if action.deadline:
                    if action.deadline.snooze_calendar_days_behind < DAYS_TO_CLOSE_INFOREQUEST:
                        break
            else:
                # Every branch that has a deadline have been missed for at least
                # DAYS_TO_CLOSE_INFOREQUEST calendar days.
                nop()  # To let tests raise testing exception here.
                filtered.append(inforequest)
        except Exception:
            msg = u'Checking if inforequest should be closed failed: {}\n{}'
            trace = traceback.format_exc()
            cron_logger.error(msg.format(inforequest, trace))

    for inforequest in filtered:
        try:
            with transaction.atomic():
                for branch in inforequest.branches:
                    branch.add_expiration_if_expired()
                inforequest.closed = True
                inforequest.save(update_fields=[u'closed'])
                nop()  # To let tests raise testing exception here.
                cron_logger.info(u'Closed inforequest: {}'.format(inforequest))
        except Exception:
            msg = u'Closing inforequest failed: {}\n{}'
            trace = traceback.format_exc()
            cron_logger.error(msg.format(inforequest, trace))

@cron_job(run_at_times=settings.CRON_IMPORTANT_MAINTENANCE_TIMES)
def publish_inforequests():
    if not settings.AUTOPUBLISH_INFOREQUESTS:
        cron_logger.info(u'Automatically publishing inforequests is disabled.')
        return

    inforequests = (Inforequest.objects
            .closed()
            .published_unknown()
            )

    filtered = []
    for inforequest in inforequests:
        days_to_publish_inforequest = inforequest.applicant.profile.days_to_publish_inforequest
        try:
            for branch in inforequest.branches:
                action = branch.last_action
                if action.deadline:
                    days_to_publish = DAYS_TO_CLOSE_INFOREQUEST + days_to_publish_inforequest
                    if action.deadline.snooze_calendar_days_behind < days_to_publish:
                        break
                else:
                    days_since_last_action = (local_today() - local_date(action.created)).days
                    if days_since_last_action < days_to_publish_inforequest:
                        break
            else:
                # We publish the inforequest after it was closed for at least
                # days_to_publish_inforequest calendar days. The inforequest was closed when all its
                # branches with deadlines had been missed for at least DAYS_TO_CLOSE_INFOREQUEST
                # calendar days. Therefore we publish it when all its branches with deadlines are
                # missed for at least DAYS_TO_CLOSE_INFOREQUEST + days_to_publish_inforequest
                # calendar days, and last actions of all its branches without deadlines were added
                # at least before days_to_publish_inforequest calendar days.
                filtered.append(inforequest)
        except Exception:
            msg = u'Checking if inforequest should be published failed: {}\n{}'
            trace = traceback.format_exc()
            cron_logger.error(msg.format(inforequest, trace))

    for inforequest in filtered:
        try:
            inforequest.published = True
            inforequest.save(update_fields=[u'published'])
            cron_logger.info(u'Published inforequest: {}'.format(inforequest))
        except Exception:
            msg = u'Publishing inforequest failed: {}\n{}'
            trace = traceback.format_exc()
            cron_logger.error(msg.format(inforequest, trace))

@cron_job(run_at_times=settings.CRON_IMPORTANT_MAINTENANCE_TIMES)
@transaction.atomic
def add_expirations():
    inforequests = (Inforequest.objects
            .not_closed()
            .without_undecided_email()
            .prefetch_related(Inforequest.prefetch_branches())
            .prefetch_related(Branch.prefetch_last_action(u'branches'))
            )

    filtered = []
    for inforequest in inforequests:
        for branch in inforequest.branches:
            try:
                action = branch.last_action
                if not action.has_obligee_deadline_snooze_missed:
                    continue
                if action.deadline.calendar_days_behind <= 8:
                    continue
                # The last action obligee deadline was missed more than 8 calendar days ago. The
                # applicant may snooze for at most 8 calendar days. So it's safe to add expiration
                # now. The expiration action has 15 calendar days deadline of which about half is
                # still left.
                filtered.append(branch)
            except Exception:
                msg = u'Checking if expiration action should be added failed: {}\n{}'
                trace = traceback.format_exc()
                cron_logger.error(msg.format(branch, trace))

    for branch in filtered:
        try:
            with transaction.atomic():
                branch.add_expiration_if_expired()
                cron_logger.info(u'Added expiration action: {}'.format(branch))
        except Exception:
            msg = u'Adding expiration action failed: {}\n{}'
            trace = traceback.format_exc()
            cron_logger.error(msg.format(branch, trace))
