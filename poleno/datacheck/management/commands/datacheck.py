# vim: expandtab
# -*- coding: utf-8 -*-
from optparse import make_option
from django.core.management.base import NoArgsCommand
from django.core.management.color import color_style
from django.utils.encoding import force_str

from ... import datacheck

class Command(NoArgsCommand):
    help = u'Runs ``datacheck`` methods on all installed models and report any found issues.'
    option_list = NoArgsCommand.option_list + (
        make_option(u'--superficial', action=u'store_true', dest=u'superficial', default=False,
            help=u'Run only siplified checks and skip any checks that may be slow.'),
        )

    def handle_noargs(self, **options):
        groups = [
                (u'CRITICALS', datacheck.CRITICAL, float(u'inf'),      color_style().ERROR),
                (u'ERRORS',    datacheck.ERROR,    datacheck.CRITICAL, color_style().ERROR),
                (u'WARNINGS',  datacheck.WARNING,  datacheck.ERROR,    color_style().WARNING),
                (u'INFOS',     datacheck.INFO,     datacheck.WARNING,  color_style().NOTICE),
                (u'DEBUGS',    0,                  datacheck.INFO,     color_style().NOTICE),
                ]

        output = []
        issues = datacheck.run_checks(options[u'superficial'])
        output.append(u'Data check identified %s issues.' % len(issues))
        for group, level_min, level_max, style in groups:
            filtered = [a for a in issues if level_min <= a.level < level_max]
            if filtered:
                output.append(u'')
                output.append(u'%s:' % group)
                output.extend(style(u'%s' % a) for a in filtered)

        self.stdout.write(u'\n'.join(output))
