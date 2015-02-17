# vim: expandtab
# -*- coding: utf-8 -*-
import datetime
import logging

from django_cron import CronJobBase, Schedule

default_app_config = 'poleno.cron.apps.CronConfig'
cron_logger = logging.getLogger(u'poleno.cron')

def cron_job(**kwargs):
    u"""
    Decorator to create a cron job class. To enable the created cron job, add it to
    ``CRON_CLASSES`` in ``settings.py``.

    Depends on: django_cron

    Arguments:
     -- run_every_mins: int
     -- run_at_times: list of 'HH:MM' srings
     -- retry_after_failure_mins: int

    Example:
        @cron_job(run_every_mins=60)
        def run_every_hour():
            pass

        @cron_job(run_at_times=['09:00'], retry_after_failure_mins=10)
        def run_every_morning():
            pass
    """
    def decorator(function):
        class CronJob(CronJobBase):
            schedule = Schedule(**kwargs)
            code = u'%s.%s' % (function.__module__.split('.')[-2], function.__name__)
            def do(self):
                return function()
        CronJob.__name__ = function.__name__
        return CronJob
    return decorator
