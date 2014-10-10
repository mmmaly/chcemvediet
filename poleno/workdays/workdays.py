# vim: expandtab
# -*- coding: utf-8 -*-
import datetime
from dateutil.easter import easter

from django.conf import settings
from django.utils.importlib import import_module


WEEKEND = [5, 6]

def _holidays():
    try:
        path = settings.HOLIDAYS_MODULE_PATH
    except AttributeError:
        return None
    module = import_module(path)
    return module.HOLIDAYS


class Holiday(object):
    def __init__(self, first_year=None, last_year=None):
        self.first_year = first_year
        self.last_year = last_year

    def between(self, after, before):
        u"""
        List of holidays in interval (after, before]
        """
        first_year = max(self.first_year, after.year) if self.first_year else after.year
        last_year = min(self.last_year, before.year) if self.last_year else before.year
        return [d for y in range(first_year, last_year+1)
                  for d in self.for_year(y)
                  if after < d <= before]

    def for_year(self, year):
        raise NotImplementedError

class FixedHoliday(Holiday):
    def __init__(self, **kwargs):
        self.day = kwargs.pop(u'day')
        self.month = kwargs.pop(u'month')
        super(FixedHoliday, self).__init__(**kwargs)

    def for_year(self, year):
        return [datetime.date(year, self.month, self.day)]

    def __repr__(self):
        return u'%s(day=%s, month=%s)' % (self.__class__.__name__, repr(self.day), repr(self.month))

class EasterHoliday(Holiday):
    def __init__(self, **kwargs):
        u"""
        ``days`` after/before Easter Sunday if positive/negative.
        """
        self.days = kwargs.pop(u'days', 0)
        super(EasterHoliday, self).__init__(**kwargs)

    def for_year(self, year):
        return [easter(year) + datetime.timedelta(days=self.days)]

    def __repr__(self):
        return u'%s(days=%s)' % (self.__class__.__name__, repr(self.days))

class HolidaySet(object):
    def __init__(self, *args):
        u"""
        Accepts Holiday objects
        """
        self.holidays = args

    def between(self, after, before):
        u"""
        Set of unique holidays in interval (after, before].
        """
        return set(d for h in self.holidays
                     for d in h.between(after, before))

    def __repr__(self):
        return u'%s%s' % (self.__class__.__name__, repr(self.holidays))


def between(after, before, holiday_set=None):
    u"""
    Returns number of working days between ``after`` and ``before`` excluding ``after`` and
    including ``before``. If ``a`` is the day we submitted something and ``b`` is today, then today
    is the last full day of a ``d`` days long deadline if: ``between(a, b) == d``, and the deadline
    is missed if: ``between(a, b) > d``.

    The following invariants hold:
        between(a, a) == 0
        between(a, b) == -between(b, a)
        between(a, b) == between(a, x) + between(x, b)
        between(a, a+1) == 1 iff a+1 is workday; 0 otherwise
    """
    if after == before:
        return 0
    if after > before:
        return -between(before, after, holiday_set)

    if not holiday_set:
        holiday_set = _holidays()
    if not holiday_set:
        raise ValueError(u'Specify holiday_set or set global setting HOLIDAYS_MODULE_PATH.')

    # Having: after < before
    days = (before - after).days
    res = (days/7)*(7-len(WEEKEND)) # Full weeks
    res += len([1 for d in range(days%7) # At most 6 iterations for the remaining partial week
                  if (before - datetime.timedelta(days=d)).weekday() not in WEEKEND])
    res -= len([1 for d in holiday_set.between(after, before)
                  if d.weekday() not in WEEKEND])
    return res

