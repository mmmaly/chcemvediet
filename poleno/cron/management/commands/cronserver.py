# vim: expandtab
# -*- coding: utf-8 -*-
import time
from textwrap import dedent
from optparse import make_option

from django.core.management import call_command
from django.core.management.base import NoArgsCommand

class Command(NoArgsCommand):
    default_interval = 60

    help = dedent(u"""\
        Dummy cron server for local development. Repeatedly calls ``runcrons`` management command
        executing all sheduled cron jobs.""")

    option_list = NoArgsCommand.option_list + (
        make_option(u'--interval', action=u'store', type=u'int', dest=u'interval', default=default_interval,
            help=u'Interval in seconds how often to check if there are jobs to run. Defaults to %d secons.' % default_interval),
        )

    def handle_noargs(self, **options):
        interval = options[u'interval']

        try:
            while True:
                call_command(u'runcrons')
                time.sleep(interval)
        except KeyboardInterrupt:
            pass
