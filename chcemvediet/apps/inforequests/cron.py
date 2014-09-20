# vim: expandtab
# -*- coding: utf-8 -*-
import datetime

from django.utils.translation import activate

from poleno.cron import cron_job
from poleno.workdays import workdays

from models import Inforequest

@cron_job(run_at_times=[u'09:00'])
def undecided_email_reminder():
    activate(u'en') # We need to select active locale ('en-us' is selected by default)
    for inforequest in Inforequest.objects.all():
        email = inforequest.newest_waiting_email
        if not email:
            continue
        last = inforequest.last_undecided_email_reminder
        if last and last > email.received_datetime:
            continue
        days = workdays.between(email.received_date, datetime.date.today())
        if days < 5:
            continue
        inforequest.send_undecided_email_reminder()
