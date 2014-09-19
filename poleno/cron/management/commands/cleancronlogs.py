# vim: expandtab
# -*- coding: utf-8 -*-
from django.core.management.base import NoArgsCommand

from django_cron.models import CronJobLog

class Command(NoArgsCommand):
    help = u'Clean cron logs.'

    def handle_noargs(self, **options):
        CronJobLog.objects.all().delete()
