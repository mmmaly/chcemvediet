# vim: expandtab
# -*- coding: utf-8 -*-
from django.utils.encoding import force_text
from django.utils.functional import lazy


def lazy_decorator(*resultclasses):
    def actual_decorator(func):
        return lazy(func, *resultclasses)
    return actual_decorator

@lazy_decorator(str)
def lazy_concat(*strings):
    return u''.join(force_text(s) for s in strings)

@lazy_decorator(str)
def lazy_format(fmt, *args, **kwargs):
    return force_text(fmt).format(*args, **kwargs)
