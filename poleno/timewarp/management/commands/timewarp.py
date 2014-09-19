# vim: expandtab
# -*- coding: utf-8 -*-
import datetime
from textwrap import dedent
from optparse import make_option
from dateutil.relativedelta import relativedelta

from django.core.management.base import BaseCommand, CommandError
from django.utils import formats

from poleno.timewarp.timewarp import timewarp

class Command(BaseCommand):
    help = dedent(u"""\
        Simulates the server is running on different dates and times. If you need to test some
        logic with long timeouts, you can use this command to simulate the time already passed
        instead of wating for it. You can jump forward and backward in time and change the rate at
        which the time flows. For instance, if you speed the time up 24 times, a day passes in one
        hour. To see the current settings just run the command with no options.

        Examples:
            timewarp 2015-10-10 11:34      Jump to the exact date and time.
            timewarp --month=2             Jump to the second month of the same year.
            timewarp --months=3 --days=4   Jump 3 months and 4 days to the future.
            timewarp --weekday=6           Jump to the next sunday.
            timewarp --speedup=-1          Make time flow backwards.
            timewarp --reset               Return back to the present.""")

    args = u"""[yyyy-mm-dd [hh:mm[:ss]]]"""

    option_list = BaseCommand.option_list + (
        make_option(u'--year', action=u'store', type=u'int', dest=u'year', default=None, help=u'Change to year.'),
        make_option(u'--month', action=u'store', type=u'int', dest=u'month', default=None, help=u'Change to month.'),
        make_option(u'--day', action=u'store', type=u'int', dest=u'day', default=None, help=u'Change to day in month.'),
        make_option(u'--hour', action=u'store', type=u'int', dest=u'hour', default=None, help=u'Change to hour.'),
        make_option(u'--minute', action=u'store', type=u'int', dest=u'minute', default=None, help=u'Change to minute.'),
        make_option(u'--second', action=u'store', type=u'int', dest=u'second', default=None, help=u'Change to second.'),

        make_option(u'--years', action=u'store', type=u'int', dest=u'years', default=None, help=u'Advance by years.'),
        make_option(u'--months', action=u'store', type=u'int', dest=u'months', default=None, help=u'Advance by months.'),
        make_option(u'--weeks', action=u'store', type=u'int', dest=u'weeks', default=None, help=u'Advance by weeks.'),
        make_option(u'--days', action=u'store', type=u'int', dest=u'days', default=None, help=u'Advance by days.'),
        make_option(u'--hours', action=u'store', type=u'int', dest=u'hours', default=None, help=u'Advance by hours.'),
        make_option(u'--minutes', action=u'store', type=u'int', dest=u'minutes', default=None, help=u'Advance by minutes.'),
        make_option(u'--seconds', action=u'store', type=u'int', dest=u'seconds', default=None, help=u'Advance by seconds.'),
        make_option(u'--weekday', action=u'store', type=u'int', dest=u'weekday', default=None, help=u'Advance to the next weekday. (0 for monday, 1 for tuesday, ...)'),

        make_option(u'--speedup', action=u'store', type=u'int', dest=u'speedup', default=None, help=u'Rate at which the time flows.'),
        make_option(u'--reset', action=u'store_true', dest=u'reset', default=False, help=u'Reset Timewarp.'),
        )

    def handle(self, *args, **options):
        #print(args, options)

        delta_options = {k: options[k] for k in [
                    u'year', u'month', u'day', u'hour', u'minute', u'second',
                    u'years', u'months', u'weeks', u'days', u'hours', u'minutes', u'seconds', u'weekday',
                    ] if options[k] is not None}

        if options[u'reset']:
            print(u'Resetting Timewarp...')
            timewarp.reset()

        elif args or delta_options or options[u'speedup'] is not None:
            print(u'Jumping...')
            if args:
                joined = u' '.join(args)
                for format in [u'%Y-%m-%d %H:%M:%S', u'%Y-%m-%d %H:%M', u'%Y-%m-%d']:
                    try:
                        date = datetime.datetime.strptime(joined, format)
                    except (ValueError, TypeError):
                        continue
                    break
                else:
                    raise CommandError(u'Invalid date: "%s".' % joined)
            else:
                # Notice that this datetime may already be warped.
                date = datetime.datetime.now()

            delta = relativedelta(**delta_options)
            timewarp.jump(date=date+delta, speed=options[u'speedup'])

        print(u'Real time: %s' % datetime.datetime.fromtimestamp(timewarp.real_time))
        print(u'Warped time: %s' % (datetime.datetime.fromtimestamp(timewarp.warped_time) if timewarp.is_warped else u'--'))
        print(u'Speedup: %s' % (timewarp.speedup if timewarp.is_warped else u'--'))

