# vim: expandtab
# -*- coding: utf-8 -*-
from datetime import timedelta

from django.db import transaction
from django_cron.models import CronJobLog

from poleno.cron import cron_job, cron_logger
from poleno.utils.date import utc_now

@cron_job(run_at_times=[u'04:00'])
@transaction.atomic
def clear_old_cronlogs():
    threshold = utc_now() - timedelta(days=7)
    CronJobLog.objects.filter(start_time__lt=threshold).delete()
    cron_logger.info(u'Cleared old cron logs.')
