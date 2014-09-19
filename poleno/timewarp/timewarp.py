# vim: expandtab
# -*- coding: utf-8 -*-
import time as time_orig
import datetime as datetime_orig

timewarp = None

class Timewarp(object):
    def __init__(self):
        from django.core.cache import cache as _cache
        self._cache = _cache
        self._recursive = False
        self._lastupdate = None
        self._warped_from = None
        self._warped_to = None
        self._speedup = 1

    def _update(self):
        if self._recursive:
            return
        if self._lastupdate and self._lastupdate + 1 > time_orig.time():
            return
        self._recursive = True
        self._warped_from = self._cache.get(u'timewarp.warped_from')
        self._warped_to = self._cache.get(u'timewarp.warped_to')
        self._speedup = self._cache.get(u'timewarp.speedup', 1)
        self._recursive = False
        self._lastupdate = time_orig.time()

    @property
    def warped_from(self):
        self._update()
        return self._warped_from

    @property
    def warped_to(self):
        self._update()
        return self._warped_to

    @property
    def speedup(self):
        self._update()
        return self._speedup

    @property
    def is_warped(self):
        return self.warped_from is not None and self.warped_to is not None

    @property
    def real_time(self):
        return time_orig.time()

    @property
    def warped_time(self):
        if self.is_warped:
            return self.warped_to + (self.real_time - self.warped_from) * self.speedup
        return self.real_time

    def jump(self, date=None, speed=None):
        self._cache.set_many({
            u'timewarp.warped_from': self.real_time,
            u'timewarp.warped_to': time_orig.mktime(date.timetuple()) if date is not None else self.warped_time,
            u'timewarp.speedup': speed if speed is not None else self.speedup,
            }, timeout=None)
        self._lastupdate = None

    def reset(self):
        self._cache.delete_many([u'timewarp.warped_from', u'timewarp.warped_to', u'timewarp.speedup'])
        self._lastupdate = None


def _meta_factory(cls):
    class Meta(cls.__class__):
        def __init__(self, *args, **kwargs):
            cls.__class__.__init__(self, *args, **kwargs)
            self.__module__ = cls.__module__

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
            secs = warped_time()
        return time_orig.ctime(secs)

    @classmethod
    def gmtime(cls, secs=None):
        if secs is None:
            secs = warped_time()
        return time_orig.gmtime(secs)

    @classmethod
    def localtime(cls, secs=None):
        if secs is None:
            secs = warped_time()
        return time_orig.localtime(secs)

    @classmethod
    def strftime(cls, format, t=None):
        if t is None:
            t = cls.localtime()
        return time_orig.strftime(format, t)

    @classmethod
    def time(cls):
        return warped_time()

    def __getattr__(self, attr):
        return getattr(time_orig, attr)

class _WarpedDatetime(object):

    class date(datetime_orig.date):
        __metaclass__ = _meta_factory(datetime_orig.date)

        def __new__(cls, *args, **kwargs):
            return datetime_orig.date(*args, **kwargs)

        @classmethod
        def today(cls):
            return datetime_orig.datetime.fromtimestamp(warped_time()).date()

    class datetime(datetime_orig.datetime):
        __metaclass__ = _meta_factory(datetime_orig.datetime)

        def __new__(cls, *args, **kwargs):
            return datetime_orig.datetime(*args, **kwargs)

        @classmethod
        def today(cls):
            return datetime_orig.datetime.fromtimestamp(warped_time())

        @classmethod
        def now(cls, tz=None):
            return datetime_orig.datetime.fromtimestamp(warped_time(), tz)

        @classmethod
        def utcnow(cls):
            return datetime_orig.datetime.utcfromtimestamp(warped_time())

    def __getattr__(self, attr):
        return getattr(datetime_orig, attr)


def init():
    import os
    import sys
    import warnings
    import copy_reg
    from django.utils.importlib import import_module

    # We may not import ``django.conf.settings`` because this would initialize ``timezone`` as
    # well. But we need ``timezone`` to be initialized only after ``datetime`` module is wrapped.
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
        copy_reg.pickle(datetime_orig.date, lambda d: (_WarpedDatetime.date,) + d.__reduce__()[1:])
        copy_reg.pickle(datetime_orig.datetime, lambda d: (_WarpedDatetime.datetime,) + d.__reduce__()[1:])

        global timewarp
        timewarp = Timewarp()

def real_time():
    return time_orig.time()

def warped_time():
    return timewarp.warped_time if timewarp else time_orig.time()
