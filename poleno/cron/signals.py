# vim: expandtab
# -*- coding: utf-8 -*-
from django.dispatch import receiver
from django.db.models.signals import post_save
from django_cron import CronJobLog

from . import cron_logger

@receiver(post_save, sender=CronJobLog)
def log_to_logger_on_cronjoblog_post_save(sender, instance, **kwargs):
    u"""
    Track saved cron logs using standard logging framework.
    """
    if instance.is_success:
        cron_logger.debug(u"Cron job '%s' succeeded.", instance.code)
    else:
        cron_logger.error(u"Cron job '%s' failed:\n%s", instance.code, instance.message)
