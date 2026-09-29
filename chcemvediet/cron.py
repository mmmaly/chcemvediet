# vim: expandtab
# -*- coding: utf-8 -*-
import os
import shutil
import datetime
from email.utils import formataddr

from django.core.mail import EmailMessage
from django.core.management import call_command
from django.conf import settings
from django.contrib.sites.models import Site
from django.db.models import Count
from django.utils import timezone
from django_cron.models import CronJobLog

from poleno.cron import cron_job, cron_logger
from poleno.mail.models import Message, Recipient
from poleno.utils.date import utc_now
from chcemvediet.apps.anonymization.models import (AttachmentNormalization, AttachmentRecognition,
        AttachmentAnonymization, AttachmentFinalization)
from chcemvediet.apps.inforequests.models import Inforequest, Action


@cron_job(run_at_times=settings.CRON_UNIMPORTANT_MAINTENANCE_TIMES)
def clear_expired_sessions():
    call_command(u'clearsessions')
    cron_logger.info(u'Cleared expired sessions.')

@cron_job(run_every_mins=60)
def send_admin_error_logs():
    logfile = os.path.join(settings.PROJECT_PATH, u'logs/mail_admins.log')
    tmpfile = logfile + u'.tmp'

    if not os.path.isfile(logfile):
        return

    # This is not multi process safe. We may lose a log entry if somebody is writing it right now.
    # Any future entries should be safely written into a new log file.
    os.rename(logfile, tmpfile)
    with open(tmpfile) as f:
        logs = f.read()
    os.remove(tmpfile)

    if not logs:
        return

    # FIXME: We should skip Mandrill and use some low level mail delivery for admin logs.
    site = Site.objects.get_current()
    subject = u'[{}] Admin Error Logs'.format(site.name)
    admins = (formataddr(r) for r in settings.ADMINS)
    msg = EmailMessage(subject, logs, settings.SERVER_EMAIL, admins)
    msg.send()

def _format_local(value):
    return timezone.localtime(value).strftime(u'%Y-%m-%d %H:%M') if value else u'never'

def _daily_status():
    u"""
    Returns ``(problems, lines)`` describing the last 24 hours of mail, cron jobs and attachment
    anonymization.
    """
    now = utc_now()
    since = now - datetime.timedelta(days=1)
    stuck_before = now - datetime.timedelta(minutes=15)
    problems = []
    lines = []

    outbound = Message.objects.outbound()
    inbound = Message.objects.inbound()
    sent = outbound.filter(processed__gte=since)
    statuses = (Recipient.objects
            .filter(message__in=sent)
            .values_list(u'status')
            .annotate(Count(u'pk'))
            .order_by(u'status'))
    queued = outbound.not_processed().count()
    stuck_outbound = outbound.not_processed().filter(created__lt=stuck_before).count()
    received = inbound.filter(created__gte=since).count()
    stuck_inbound = inbound.not_processed().filter(created__lt=stuck_before).count()
    last_inbound = inbound.order_by(u'-created').values_list(u'created', flat=True).first()
    error_mails = sent.filter(subject__endswith=u'Admin Error Logs').count()

    lines.append(u'Mail')
    lines.append(u'  Outbound sent: {} (recipients: {})'.format(sent.count(), u', '.join(
            u'{} {}'.format(Recipient.STATUSES._inverse[s].split(u'.')[-1].lower(), c)
            for s, c in statuses) or u'none'))
    lines.append(u'  Outbound queue: {} (older than 15 minutes: {})'.format(queued, stuck_outbound))
    lines.append(u'  Inbound received: {} (unprocessed older than 15 minutes: {})'.format(
            received, stuck_inbound))
    lines.append(u'  Last inbound message: {}'.format(_format_local(last_inbound)))
    lines.append(u'  Admin error log e-mails: {}'.format(error_mails))
    rejected = sum(c for s, c in statuses
            if s in (Recipient.STATUSES.REJECTED, Recipient.STATUSES.INVALID))
    if rejected:
        problems.append(u'{} outbound recipients rejected or invalid'.format(rejected))
    if stuck_outbound:
        problems.append(u'{} outbound messages waiting longer than 15 minutes'.format(
                stuck_outbound))
    if stuck_inbound:
        problems.append(u'{} inbound messages unprocessed longer than 15 minutes'.format(
                stuck_inbound))
    # Gaps of up to 4 days without inbound mail are normal (2025-2026).
    if last_inbound is None or last_inbound < now - datetime.timedelta(days=5):
        problems.append(u'no inbound message for more than 5 days')
    if error_mails:
        problems.append(u'{} admin error log e-mails sent'.format(error_mails))

    runs = CronJobLog.objects.filter(start_time__gte=since)
    failed = (runs.filter(is_success=False)
            .values_list(u'code')
            .annotate(Count(u'pk'))
            .order_by(u'code'))
    lines.append(u'Cron jobs')
    lines.append(u'  Runs: {}, failed: {}'.format(runs.count(), sum(c for _, c in failed)))
    for code, count in failed:
        lines.append(u'  Failed {}: {}'.format(code, count))
        problems.append(u'cron job {} failed {} times'.format(code, count))

    # Some attachments always fail (about 15 % in 2026: unsupported formats, OCR refusals), so
    # failures are reported but not counted as problems.
    lines.append(u'Attachment anonymization (successful / failed)')
    for model in (AttachmentNormalization, AttachmentRecognition, AttachmentAnonymization,
            AttachmentFinalization):
        stages = model.objects.filter(created__gte=since)
        ok = stages.filter(successful=True).count()
        bad = stages.filter(successful=False).count()
        lines.append(u'  {}: {} / {}'.format(model.__name__, ok, bad))

    lines.append(u'Activity')
    lines.append(u'  New inforequests: {}, new actions: {}'.format(
            Inforequest.objects.filter(submission_date__gte=timezone.localdate(since)).count(),
            Action.objects.filter(created__gte=since).count()))

    usage = shutil.disk_usage(settings.MEDIA_ROOT)
    free_percent = 100.0 * usage.free / usage.total
    lines.append(u'Disk')
    lines.append(u'  Free: {:.0f} GB ({:.0f} %)'.format(usage.free / 1e9, free_percent))
    if free_percent < 10:
        problems.append(u'only {:.0f} % disk space free'.format(free_percent))

    return problems, lines

@cron_job(run_at_times=settings.CRON_DAILY_STATUS_TIMES)
def send_daily_status():
    u"""
    Sends admins a short report about the last 24 hours every day, even if everything is fine. The
    report goes through the regular outbound mail queue, so its arrival shows that outbound mail
    and cron jobs work; a missing report is itself a warning.
    """
    problems, lines = _daily_status()
    site = Site.objects.get_current()
    if problems:
        subject = u'[{}] Daily status: {} problem(s)'.format(site.name, len(problems))
        head = [u'Problems:'] + [u'  - {}'.format(p) for p in problems]
    else:
        subject = u'[{}] Daily status: OK'.format(site.name)
        head = [u'No problems found.']
    body = u'\n'.join(
            [u'Status of {} for the last 24 hours, {}.'.format(site.domain,
                _format_local(utc_now())), u''] + head + [u''] + lines) + u'\n'
    admins = (formataddr(r) for r in settings.ADMINS)
    msg = EmailMessage(subject, body, settings.SERVER_EMAIL, admins)
    msg.send()
    cron_logger.info(u'Sent daily status: {}'.format(subject))
