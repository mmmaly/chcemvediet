# vim: expandtab
# -*- coding: utf-8 -*-
from django.utils import timezone

# All functions assume that settings.USE_TZ is True.

def utc_now():
    u"""
    Returns aware ``datetime`` representing current time in UTC.
    """
    return timezone.now()

def local_now(tz=None):
    u"""
    Returns aware ``datetime`` representing current time in timezone ``tz``, by default the current
    time zone.
    """
    return timezone.localtime(timezone.now(), tz)

def utc_today():
    u"""
    Returns ``date`` representing current day in UTC.
    """
    return timezone.now().date()

def local_today(tz=None):
    u"""
    Returns ``date`` representing current day in timezone ``tz``, by default the current time zone.
    """
    return timezone.localtime(timezone.now(), tz).date()

def utc_date(dt):
    u"""
    Converts aware ``datetime`` ``dt`` to UTC and returns its day as ``date``.
    """
    return timezone.localtime(dt, timezone.utc).date()

def local_date(dt, tz=None):
    u"""
    Converts aware ``datetime`` ``dt`` to timezone ``tz``, by default the current time zone, and
    returns its day as ``date``.
    """
    return timezone.localtime(dt, tz).date()
