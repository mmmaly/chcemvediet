# vim: expandtab
# -*- coding: utf-8 -*-
import datetime

from django.conf import settings

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
