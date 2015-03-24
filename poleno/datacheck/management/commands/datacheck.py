# vim: expandtab
# -*- coding: utf-8 -*-
from optparse import make_option
from django.core.management.base import BaseCommand
from django.core.management.color import color_style

from ... import datacheck

class Command(BaseCommand):
    help = u'Runs all registered data checks and report any issues found. Use prefixes to filter checks by name.'
    args = u'[prefix] ...'
    option_list = BaseCommand.option_list + (
        make_option(u'--list', action=u'store_true', dest=u'list', default=False,
            help=u'Print registered checks.'),
        make_option(u'--superficial', action=u'store_true', dest=u'superficial', default=False,
            help=u'Run only siplified checks and skip any checks that may be slow.'),
        make_option(u'--autofix', action=u'store_true', dest=u'autofix', default=False,
            help=u'Automatically fix trivial issues.'),
        )

    def handle(self, *prefixes, **options):
        groups = [
                (u'CRITICALS', datacheck.CRITICAL, float(u'inf'),      color_style().ERROR),
                (u'ERRORS',    datacheck.ERROR,    datacheck.CRITICAL, color_style().ERROR),
                (u'WARNINGS',  datacheck.WARNING,  datacheck.ERROR,    color_style().WARNING),
                (u'INFOS',     datacheck.INFO,     datacheck.WARNING,  color_style().NOTICE),
                (u'DEBUGS',    0,                  datacheck.INFO,     color_style().NOTICE),
                ]

        output = []
        if options[u'list']:
            output.append(u'Available data checks:')
            output.extend(u' -- %s' % c for c in datacheck.registry)
            self.stdout.write(u'\n'.join(output))
            return

        if prefixes:
            registry = datacheck.registry.filtered(prefixes)
            output.append(u'Running %s data checks:' % len(registry))
            output.extend(u' -- %s' % c for c in registry)
            output.append(u'')
        else:
            registry = datacheck.registry
            output.append(u'Running all registered data checks.')
            output.append(u'')

        issues = registry.run_checks(superficial=options[u'superficial'], autofix=options[u'autofix'])
        autofixable = len([s for s in issues if s.autofixable])
        if autofixable:
            if options[u'autofix']:
                output.append(u'Data checks identified %s issues, %s of them were autofixed.' % (len(issues), autofixable))
            else:
                output.append(u'Data checks identified %s issues, %s of them can be autofixed (use --autofix).' % (len(issues), autofixable))
        else:
            output.append(u'Data checks identified %s issues.' % len(issues))

        for group, level_min, level_max, style in groups:
            filtered = [a for a in issues if level_min <= a.level < level_max]
            if filtered:
                output.append(u'')
                output.append(u'%s:' % group)
                output.extend(style(u'%s' % a) for a in filtered)

        self.stdout.write(u'\n'.join(output))
