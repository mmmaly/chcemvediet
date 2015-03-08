# vim: expandtab
# -*- coding: utf-8 -*-
from logging import DEBUG, INFO, WARNING, ERROR, CRITICAL

from django.apps import apps

class Issue(object):

    def __init__(self, level, msg, *args):
        self.level = level
        self.msg = msg % args
        self.model = None

    def __eq__(self, other):
        return self.level == other.level and self.msg == other.msg and self.model == other.model

    def __ne__(self, other):
        return not (self == other)

    def __unicode__(self):
        return u'%s.%s: %s' % (self.model._meta.app_label, self.model._meta.object_name, self.msg)

    def __repr__(self):
        return u'<%s: level=%r model=%s.%s msg=%r>' % (self.__class__.__name__, self.level,
                self.model._meta.app_label, self.model._meta.object_name, self.msg)

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


def run_checks(superficial=False):
    u"""
    Calls ``datacheck`` methods on all installed models and collects any reported issues. Pass
    ``superficial=True`` to run only siplified checks and skip any checks that may be slow.
    """
    issues = []
    for app in apps.get_app_configs():
        for model in app.get_models():
            if not hasattr(model, u'datacheck'):
                continue
            for issue in model.datacheck(superficial):
                issue.model = model
                issues.append(issue)
    return issues
