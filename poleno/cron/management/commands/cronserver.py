# vim: expandtab
# -*- coding: utf-8 -*-
import time
from textwrap import dedent

from django.core.management import call_command
from django.core.management.base import BaseCommand
from poleno.utils.date import utc_now
from poleno.utils.misc import squeeze

from django_cron.models import CronJobLog


class Command(BaseCommand):
    default_interval = 60

    help = dedent(u"""\
        Dummy cron server for local development. Repeatedly calls ``runcrons`` management command
        executing all sheduled cron jobs.""")

    def add_arguments(self, parser):
        parser.add_argument(u'--interval', action=u'store', type=int, dest=u'interval',
            default=self.default_interval, help=squeeze(u"""
                Interval in seconds how often to check if there are jobs to run. Defaults to {}
                secons.
                """).format(self.default_interval))
        parser.add_argument(u'--clearlogs', action=u'store_true', dest=u'clearlogs',
            default=False, help=squeeze(u"""
                Clear cron logs before running the server like no cron jobs have ever been run yet.
                """))

    def handle(self, *args, **options):
        interval = options[u'interval']
        clearlogs = options[u'clearlogs']

        try:
            if clearlogs:
                CronJobLog.objects.all().delete()
            while True:
                # If we are timewarping, we may encounter cron logs from future. We must remove
                # them, otherwise django_cron won't run any jobs with logs from furure.
                CronJobLog.objects.filter(end_time__gt=utc_now()).delete()

                call_command(u'runcrons')
                time.sleep(interval)
        except KeyboardInterrupt:
            pass
