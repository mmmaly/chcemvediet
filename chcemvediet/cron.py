# vim: expandtab
# -*- coding: utf-8 -*-
from django.core.management import call_command

from poleno.cron import cron_job

@cron_job(run_every_mins=5)
def get_mail():
    call_command(u'getmail')
