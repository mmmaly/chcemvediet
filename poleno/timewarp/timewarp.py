# vim: expandtab
# -*- coding: utf-8 -*-
import time as time_orig
import datetime as datetime_orig

# Timestamps
warped_from = None
warped_to = None
speedup = 1


def _warped_time_time():
    res = time_orig.time()
    if warped_from is not None:
        res = warped_to + (res - warped_from) * speedup
    return res

def _meta_factory(cls):
    class Meta(cls.__class__):
        def __instancecheck__(self, instance):
            return isinstance(instance, cls)

        def __subclasscheck__(self, subclass):
            return issubclass(subclass, cls)

    return Meta

class _WarpedTime(object):

    @classmethod
    def asctime(cls, t=None):
        if t is None:
            t = cls.localtime()
        return time_orig.asctime(t)

    @classmethod
    def ctime(cls, secs=None):
        if secs is None:
            secs = _warped_time_time()
        return time_orig.ctime(secs)

    @classmethod
    def gmtime(cls, secs=None):
        if secs is None:
            secs = _warped_time_time()
        return time_orig.gmtime(secs)

    @classmethod
    def localtime(cls, secs=None):
        if secs is None:
            secs = _warped_time_time()
        return time_orig.localtime(secs)

    @classmethod
    def strftime(cls, format, t=None):
        if t is None:
            t = cls.localtime()
        return time_orig.strftime(format, t)

    @classmethod
    def time(cls):
        return _warped_time_time()

    def __getattr__(self, attr):
        return getattr(time_orig, attr)

class _WarpedDatetime(object):

    class date(datetime_orig.date):
        __metaclass__ = _meta_factory(datetime_orig.date)

        @classmethod
        def today(cls):
            return datetime_orig.datetime.fromtimestamp(_warped_time_time()).date()

    class datetime(datetime_orig.datetime):
        __metaclass__ = _meta_factory(datetime_orig.datetime)

        @classmethod
        def today(cls):
            return datetime_orig.datetime.fromtimestamp(_warped_time_time())

        @classmethod
        def now(cls, tz=None):
            return datetime_orig.datetime.fromtimestamp(_warped_time_time(), tz)

        @classmethod
        def utcnow(cls):
            return datetime_orig.datetime.utcfromtimestamp(_warped_time_time())

    def __getattr__(self, attr):
        return getattr(datetime_orig, attr)


def init():
    import os
    import sys
    import warnings
    from django.utils.importlib import import_module

    env_name = u'DJANGO_SETTINGS_MODULE'
    try:
        settings_path = os.environ[env_name]
    except KeyError:
        warnings.warn(RuntimeWarning(u'Timewarp could not find `%s` environment variable. Timewarp disabled.' % env_name))
        return

    try:
        settings = import_module(settings_path)
    except ImportError:
        warnings.warn(RuntimeWarning(u'Timewarp could not import settings module. Timewarp disabled.'))
        return

    # Timewarp MUST NOT be enabled if DEBUG is not True.
    if settings.DEBUG:
        sys.modules[u'time'] = _WarpedTime()
        sys.modules[u'datetime'] = _WarpedDatetime()

def jump(date=None, speed=None):
    global warped_from, warped_to, speedup

    # ``warped_to`` must be set before ``warped_from``
    warped_to = time_orig.mktime(date.timetuple()) if date is not None else _warped_time_time()
    warped_from = time_orig.time()
    speedup = speed if speed is not None else speedup

def reset():
    global warped_from, warped_to, speedup

    warped_from = None
    warped_to = None
    speedup = 1

def is_warped():
    return warped_from is not None

def time_real():
    return time_orig.time()

def time_warped():
    return _warped_time_time()
