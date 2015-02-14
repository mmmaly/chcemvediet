# vim: expandtab
# -*- coding: utf-8 -*-
from django.core.management import call_command

from poleno.cron import cron_job, cron_logger

@cron_job(run_at_times=[u'04:00'])
def clear_expired_sessions():
    call_command(u'clearsessions')
    cron_logger.info(u'Cleared expired sessions.')
