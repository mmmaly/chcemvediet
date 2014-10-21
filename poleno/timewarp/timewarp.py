# vim: expandtab
# -*- coding: utf-8 -*-
import sys
import time as time_orig
import datetime as datetime_orig
import copy_reg

from django.core.cache import cache


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
            secs = timewarp.warped_time
        return time_orig.ctime(secs)

    @classmethod
    def gmtime(cls, secs=None):
        if secs is None:
            secs = timewarp.warped_time
        return time_orig.gmtime(secs)

    @classmethod
    def localtime(cls, secs=None):
        if secs is None:
            secs = timewarp.warped_time
        return time_orig.localtime(secs)

    @classmethod
    def strftime(cls, format, t=None):
        if t is None:
            t = cls.localtime()
        return time_orig.strftime(format, t)

    @classmethod
    def time(cls):
        return timewarp.warped_time

    def __getattr__(self, attr):
        return getattr(time_orig, attr)

class _WarpedDatetime(object):

    class date(datetime_orig.date):
        __metaclass__ = _meta_factory(datetime_orig.date)

        def __new__(cls, *args, **kwargs):
            return datetime_orig.date(*args, **kwargs)

        @classmethod
        def today(cls):
            return datetime_orig.datetime.fromtimestamp(timewarp.warped_time).date()

    class datetime(datetime_orig.datetime):
        __metaclass__ = _meta_factory(datetime_orig.datetime)

        def __new__(cls, *args, **kwargs):
            return datetime_orig.datetime(*args, **kwargs)

        @classmethod
        def today(cls):
            return datetime_orig.datetime.fromtimestamp(timewarp.warped_time)

        @classmethod
        def now(cls, tz=None):
            return datetime_orig.datetime.fromtimestamp(timewarp.warped_time, tz)

        @classmethod
        def utcnow(cls):
            return datetime_orig.datetime.utcfromtimestamp(timewarp.warped_time)

    def __getattr__(self, attr):
        return getattr(datetime_orig, attr)


class Timewarp(object):
    def __init__(self):
        self._enabled = False
        self._recursive = False
        self._lastupdate = None
        self._warped_from = None
        self._warped_to = None
        self._speedup = 1

        self._time_warped = _WarpedTime()
        self._datetime_warped = _WarpedDatetime()

        self._remap = (
            (time_orig, self._time_warped),
            (time_orig.asctime, self._time_warped.asctime),
            (time_orig.ctime, self._time_warped.ctime),
            (time_orig.gmtime, self._time_warped.gmtime),
            (time_orig.localtime, self._time_warped.localtime),
            (time_orig.strftime, self._time_warped.strftime),
            (time_orig.time, self._time_warped.time),
            (datetime_orig, self._datetime_warped),
            (datetime_orig.date, self._datetime_warped.date),
            (datetime_orig.datetime, self._datetime_warped.datetime),
            )

    def enable(self):
        if not self._enabled:
            self._enabled = True
            self._remap_modules({a: b for a, b in self._remap})
            copy_reg.pickle(datetime_orig.date, lambda d: (_WarpedDatetime.date,) + d.__reduce__()[1:])
            copy_reg.pickle(datetime_orig.datetime, lambda d: (_WarpedDatetime.datetime,) + d.__reduce__()[1:])

    def disable(self):
        if self._enabled:
            self._enabled = False
            self._remap_modules({b: a for a, b in self._remap})
            copy_reg.pickle(datetime_orig.date, lambda d: d.__reduce__())
            copy_reg.pickle(datetime_orig.datetime, lambda d: d.__reduce__())

    def _remap_modules(self, remap):
        for name, module in sys.modules.items():
            if module is None:
                continue
            if name == __name__: # Skip this module
                continue
            if module in remap:
                sys.modules[name] = remap[module]
                continue
            for var, value in module.__dict__.items():
                try:
                    if value in remap:
                        setattr(module, var, remap[value])
                except TypeError:
                    pass

    @property
    def _time_orig(self):
        return time_orig

    @property
    def _datetime_orig(self):
        return datetime_orig

    def _update(self):
        if self._recursive:
            return
        if self._lastupdate and self._lastupdate + 1 > time_orig.time():
            return
        self._recursive = True
        self._warped_from = cache.get(u'timewarp.warped_from')
        self._warped_to = cache.get(u'timewarp.warped_to')
        self._speedup = cache.get(u'timewarp.speedup', 1)
        self._recursive = False
        self._lastupdate = time_orig.time()

    @property
    def warped_from(self):
        if not self._enabled:
            return None
        self._update()
        return self._warped_from

    @property
    def warped_to(self):
        if not self._enabled:
            return None
        self._update()
        return self._warped_to

    @property
    def speedup(self):
        if not self._enabled:
            return 1
        self._update()
        return self._speedup

    @property
    def is_warped(self):
        return self.warped_to is not None

    @property
    def real_time(self):
        return time_orig.time()

    @property
    def warped_time(self):
        if self.is_warped:
            return self.warped_to + (self.real_time - self.warped_from) * self.speedup
        return self.real_time

    def jump(self, date=None, speed=None):
        if not self._enabled:
            raise RuntimeError(u'Timewarp is disabled.')
        cache.set_many({
            u'timewarp.warped_from': self.real_time,
            u'timewarp.warped_to': time_orig.mktime(date.timetuple()) if date is not None else self.warped_time,
            u'timewarp.speedup': speed if speed is not None else self.speedup,
            }, timeout=None)
        self._lastupdate = None

    def reset(self):
        cache.delete_many([u'timewarp.warped_from', u'timewarp.warped_to', u'timewarp.speedup'])
        self._lastupdate = None

timewarp = Timewarp()
