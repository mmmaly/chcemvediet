# vim: expandtab
# -*- coding: utf-8 -*-
from django.core.management.base import BaseCommand

from django_cron.models import CronJobLog


class Command(BaseCommand):
    help = u'Clean cron logs.'

    def handle(self, *args, **options):
        CronJobLog.objects.all().delete()
