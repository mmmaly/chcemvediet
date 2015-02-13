# vim: expandtab
# -*- coding: utf-8 -*-
from textwrap import dedent

from django.core.management.base import NoArgsCommand

from django_cron.models import CronJobLog
from django_cron.management.commands.runcrons import Command as OriginalCommand

from poleno.utils.date import utc_now

class Command(OriginalCommand):
    help = dedent(u"""\
        Fixed django_cron ``runcrons`` command working with timewarp. If we are timewarping, we may
        encounter cron logs from future. We must remove them, otherwise django_cron won't run any
        jobs with logs from furure.""")

    def handle(self, *args, **options):
        CronJobLog.objects.filter(end_time__gt=utc_now()).delete()
        super(Command, self).handle(*args, **options)
