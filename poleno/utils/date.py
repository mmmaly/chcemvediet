# vim: expandtab
# -*- coding: utf-8 -*-
import datetime

from django.utils import timezone

from poleno.utils.misc import overloaded

# All functions assume that settings.USE_TZ is True.

def local_now(tz=None):
    u"""
    Returns aware ``datetime`` in timezone ``tz``, by default the current timezone, representing
    current time.

    Usage:
        local_now([tz])
    """
    dt = timezone.localtime(timezone.now(), tz)
    return dt

def local_datetime(*args, **kwargs):
    u"""
    Returns aware ``datetime`` in timezone ``tz``, by default the current timezone, representing
    the same point in time as the given day and time. The day and time may be given as an aware
    ``datetime`` or a combination of naive ``date`` and aware ``time``. The naive ``date`` may be
    given in its expanded form.

    Usage:
        local_datetime(aware_datetime, [tz])
        local_datetime(date, aware_time, [tz])
        local_datetime(year, month, day, aware_time, [tz])
    """
    tz = kwargs.pop(u'tz', None)
    dt = _datetime_factory(*args, **kwargs)
    assert timezone.is_aware(dt)
    dt = timezone.localtime(dt, tz)
    return dt

def local_datetime_from_local(*args, **kwargs):
    u"""
    Returns aware ``datetime`` in timezone ``tz``, by default the current timezone, representing
    the same point in time as the given day and time. The day and time may be given as a naive
    ``datetime`` or a combination of naive ``date`` and naive ``time``. Both naive ``date`` and
    naive ``time`` may be given in their expanded forms. The given point in time is assumed to be
    in timezone ``from_tz``, by default the current timezone.

    Usage:
        local_datetime_from_local(naive_datetime, [from_tz], [tz])
        local_datetime_from_local(date, naive_time, [from_tz], [tz])
        local_datetime_from_local(date, [hour], [minute], [second], [microsecond], [from_tz], [tz])
        local_datetime_from_local(year, month, day, naive_time, [from_tz], [tz])
        local_datetime_from_local(year, month, day, [hour], [minute], [second], [microsecond], [from_tz], [tz])
    """
    from_tz = kwargs.pop(u'from_tz', timezone.get_current_timezone())
    tz = kwargs.pop(u'tz', None)
    dt = _datetime_factory(*args, **kwargs)
    assert timezone.is_naive(dt)
    dt = dt.replace(tzinfo=from_tz)
    dt = timezone.localtime(dt, tz)
    return dt

def local_datetime_from_utc(*args, **kwargs):
    u"""
    Returns aware ``datetime`` in timezone ``tz``, by default the current timezone, representing
    the same point in time as the given day and time. The day and time may be given as a naive
    ``datetime`` or a combination of naive ``date`` and naive ``time``. Both naive ``date`` and
    naive ``time`` may be given in their expanded forms. The given point in time is assumed to be
    in UTC.

    Usage:
        local_datetime_from_utc(naive_datetime, [tz])
        local_datetime_from_utc(date, naive_time, [tz])
        local_datetime_from_utc(date, [hour], [minute], [second], [microsecond], [tz])
        local_datetime_from_utc(year, month, day, naive_time, [tz])
        local_datetime_from_utc(year, month, day, [hour], [minute], [second], [microsecond], [tz])
    """
    return local_datetime_from_local(from_tz=timezone.utc, *args, **kwargs)

def utc_now():
    u"""
    Returns aware ``datetime`` in UTC representing current time.

    Usage:
        utc_now()
    """
    return timezone.now()

def utc_datetime(*args, **kwargs):
    u"""
    Returns aware ``datetime`` in UTC representing the same point in time as the given day and
    time. The day and time may be given as an aware ``datetime`` or a combination of naive ``date``
    and aware ``time``. The naive ``date`` may be given in its expanded form.

    Usage:
        utc_datetime(aware_datetime)
        utc_datetime(date, [aware_time)
        utc_datetime(year, month, day, [aware_time])
    """
    return local_datetime(tz=timezone.utc, *args, **kwargs)

def utc_datetime_from_local(*args, **kwargs):
    u"""
    Returns aware ``datetime`` in UTC representing the same point in time as the given day and
    time. The day and time may be given as a naive ``datetime`` or a combination of naive ``date``
    and naive ``time``. Both naive ``date`` and naive ``time`` may be given in their expanded
    forms. The given point in time is assumed to be in timezone ``from_tz``, by default the current
    timezone.

    Usage:
        utc_datetime_from_local(naive_datetime, [from_tz])
        utc_datetime_from_local(date, naive_time, [from_tz])
        utc_datetime_from_local(date, [hour], [minute], [second], [microsecond], [from_tz])
        utc_datetime_from_local(year, month, day, naive_time, [from_tz])
        utc_datetime_from_local(year, month, day, [hour], [minute], [second], [microsecond], [from_tz])
    """
    return local_datetime_from_local(tz=timezone.utc, *args, **kwargs)

def utc_datetime_from_utc(*args, **kwargs):
    u"""
    Returns aware ``datetime`` in UTC representing the same point in time as the given day and
    time. The day and time may be given as a naive ``datetime`` or a combination of naive ``date``
    and naive ``time``. Both naive ``date`` and naive ``time`` may be given in their expanded
    forms. The given point in time is assumed to be in UTC.

    Usage:
        utc_datetime_from_utc(naive_datetime)
        utc_datetime_from_utc(date, naive_time)
        utc_datetime_from_utc(date, [hour], [minute], [second], [microsecond])
        utc_datetime_from_utc(year, month, day, naive_time)
        utc_datetime_from_utc(year, month, day, [hour], [minute], [second], [microsecond])
    """
    return local_datetime_from_local(from_tz=timezone.utc, tz=timezone.utc, *args, **kwargs)


def local_today(tz=None):
    u"""
    Returns ``date`` representing current day in timezone ``tz``, by default the current timezone.

    Usage:
        local_today([tz])
    """
    return timezone.localtime(timezone.now(), tz).date()

def local_date(*args, **kwargs):
    u"""
    Returns ``date`` part of the given point in time converted to timezone ``tz``, by default the
    current timezone. The point in time may be given as an aware ``datetime`` or a combination of
    naive ``date`` and aware ``time``. The naive ``date`` may be given in its expanded form.

    Usage:
        local_date(aware_datetime, [tz])
        local_date(date, aware_time, [tz])
        local_date(year, month, day, aware_time, [tz])
    """
    return local_datetime(*args, **kwargs).date()

def utc_today():
    u"""
    Returns ``date`` representing current day in UTC.

    Usage:
        utc_today()
    """
    return timezone.now().date()

def utc_date(*args, **kwargs):
    u"""
    Returns ``date`` part of the given point in time converted to UTC. The point in time may be
    given as an aware ``datetime`` or a combination of naive ``date`` and aware ``time``. The naive
    ``date`` may be given in its expanded form.

    Usage:
        utc_date(naive_datetime)
        utc_date(date, naive_time)
        utc_date(month, day, aware_time, naive_time)
    """
    return utc_datetime(*args, **kwargs).date()

def naive_date(*args, **kwargs):
    u"""
    Returns naive ``date`` representing the same day as the date part of the given day and time.
    The day and time may be given as a naive ``datetime`` or a combination of naive ``date`` and
    naive ``time``. Both naive ``date`` and naive ``time`` may be given in their expanded forms.
    The time part of the given value is ignored.

    Usage:
        naive_date(naive_datetime)
        naive_date(date, naive_time)
        naive_date(date, [hour], [minute], [second], [microsecond])
        naive_date(year, month, day, naive_time)
        naive_date(year, month, day, [hour], [minute], [second], [microsecond])
    """
    dt = _datetime_factory(*args, **kwargs)
    assert timezone.is_naive(dt)
    return dt.date()


def _datetime_factory(*args, **kwargs):
    u"""
    Creates ``datetime`` instance from given date and time parts.

    Usage:
        _datetime_factory(datetime)
        _datetime_factory(date, time)
        _datetime_factory(date, [hour], [minute], [second], [microsecond])
        _datetime_factory(year, month, day, time)
        _datetime_factory(year, month, day, [hour], [minute], [second], [microsecond])
    """
    args = list(args)
    nop = object()

    def pop_arg(name, typ, error=None, default=nop):
        if name in kwargs:
            return kwargs.pop(name)
        if args and isinstance(args[0], typ):
            return args.pop(0)
        if default is not nop:
            return default
        raise TypeError(u'Expecting argument: %s' % (error or name))

    dt = pop_arg(u'datetime', datetime.datetime, default=None)
    if dt is None:
        date = pop_arg(u'date', datetime.date, default=None)
        if date is None:
            year = pop_arg(u'year', int, error=u'datetime, date or year')
            month = pop_arg(u'month', int)
            day = pop_arg(u'day', int)
            date = datetime.date(year, month, day)
        time = pop_arg(u'time', datetime.time, default=None)
        if time is None:
            hour = pop_arg(u'hour', int, default=0, error=u'time or hour')
            minute = pop_arg(u'minute', int, default=0)
            second = pop_arg(u'second', int, default=0)
            microsecond = pop_arg(u'microsecond', int, default=0)
            time = datetime.time(hour, minute, second, microsecond)
        dt = datetime.datetime.combine(date, time)

    if args or kwargs:
        error = [u'%r' % a for a in args]
        error += [u'%s=%r' % (k, v) for k, v in kwargs.items()]
        raise TypeError(u'Unexpected arguments: %s' % u', '.join(error))
    return dt
