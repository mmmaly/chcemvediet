# vim: expandtab
# -*- coding: utf-8 -*-
import os
from email.utils import formataddr

from django.core.mail import EmailMessage
from django.core.management import call_command
from django.conf import settings
from django.contrib.sites.models import Site

from poleno.cron import cron_job, cron_logger

@cron_job(run_at_times=[u'04:00'])
def clear_expired_sessions():
    call_command(u'clearsessions')
    cron_logger.info(u'Cleared expired sessions.')

@cron_job(run_every_mins=60)
def send_admin_error_logs():
    logfile = os.path.abspath(os.path.join(os.path.dirname(__file__), u'../logs/mail_admins.log'))
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
    subject = u'[%s] Admin Error Logs' % site.name
    admins = (formataddr(r) for r in settings.ADMINS)
    msg = EmailMessage(subject, logs, settings.SERVER_EMAIL, admins)
    msg.send()
