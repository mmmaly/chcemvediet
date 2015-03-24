# vim: expandtab
# -*- coding: utf-8 -*-
import functools
from logging import DEBUG, INFO, WARNING, ERROR, CRITICAL

class Issue(object):

    def __init__(self, level, msg, *args, **kwargs):
        self.level = level
        self.msg = msg % args
        self.issuer = None
        self.autofixable = kwargs.pop(u'autofixable', False)
        self.autofixed = None

    def __eq__(self, other):
        return self.level == other.level and self.msg == other.msg and self.issuer == other.issuer

    def __ne__(self, other):
        return not self.__eq__(other)

    def __unicode__(self):
        return u'%s: %s%s' % (self.issuer, self.msg,
                u' (Was autofixed)' if self.autofixed else
                u' (Can be autofixed, use --autofix)' if self.autofixable else u'',
                )

    def __repr__(self):
        return u'<%s: level=%r issuer=%s msg=%r%s>' % (
                self.__class__.__name__, self.level, self.issuer, self.msg,
                u' autofixed' if self.autofixed else u' autofixable' if self.autofixable else u'',
                )

class Debug(Issue):
    def __init__(self, *args, **kwargs):
        super(Debug, self).__init__(DEBUG, *args, **kwargs)

class Info(Issue):
    def __init__(self, *args, **kwargs):
        super(Info, self).__init__(INFO, *args, **kwargs)

class Warning(Issue):
    def __init__(self, *args, **kwargs):
        super(Warning, self).__init__(WARNING, *args, **kwargs)

class Error(Issue):
    def __init__(self, *args, **kwargs):
        super(Error, self).__init__(ERROR, *args, **kwargs)

class Critical(Issue):
    def __init__(self, *args, **kwargs):
        super(Critical, self).__init__(CRITICAL, *args, **kwargs)


@functools.total_ordering
class Check(object):

    def __init__(self, func):
        self.func = func
        self.name = u'%s.%s' % (func.__module__, func.__name__)

    def __call__(self, *args, **kwargs):
        return self.func(*args, **kwargs)

    def __eq__(self, other):
        return self.func == other.func

    def __ne__(self, other):
        return not self.__eq__(other)

    def __lt__(self, other):
        return self.name < other.name

    def __unicode__(self):
        return self.name

    def __repr__(self):
        return u'<%s: %s>' % (self.__class__.__name__, self.name)

class Registry(object):

    def __init__(self):
        self.checks = set()

    def __iter__(self):
        return iter(sorted(self.checks))

    def __len__(self):
        return len(self.checks)

    def register(self, func):
        u"""
        Registers ``func`` as a data check. Can be used as a decorator.
        """
        self.checks.add(Check(func))
        return func

    def filtered(self, prefixes):
        res = Registry()
        prefixes = tuple(p + u'.' for p in prefixes)
        for check in self:
            if not prefixes or (check.name + u'.').startswith(prefixes):
                res.checks.add(check)
        return res

    def run_checks(self, superficial=False, autofix=False):
        u"""
        Run registered checks and collect reported issues. Pass ``superficial=True`` to run only
        siplified checks and skip any checks that may be slow. Pass ``autofix=True`` to
        automatically fix trivial issues.
        """
        issues = []
        for check in self:
            for issue in check(superficial=superficial, autofix=autofix):
                issue.issuer = check
                issue.autofixed = autofix and issue.autofixable
                issues.append(issue)
        return issues

registry = Registry()
register = registry.register
