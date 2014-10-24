# vim: expandtab
# -*- coding: utf-8 -*-
import datetime
import mock
import pytz
from testfixtures import test_datetime

from django.utils import timezone
from django.test import TestCase

from poleno.utils.date import local_now, local_datetime, local_datetime_from_local, local_datetime_from_utc
from poleno.utils.date import utc_now, utc_datetime, utc_datetime_from_local, utc_datetime_from_utc
from poleno.utils.date import local_today, local_date, utc_today, utc_date, naive_date

class DateTest(TestCase):
    u"""
    Tests ``local_*()``, ``utc_*()`` and ``naive_date()`` functions. Checks that computed dates and
    datetimes are corrent, are of correct types and have correct timezones set.
    """

    def setUp(self):
        self.timezone_override = timezone.override(u'Europe/Bratislava') # Fix local timezone
        self.timezone_override.__enter__()

    def tearDown(self):
        self.timezone_override.__exit__(None, None, None)


    def _parse_dt(self, value, tzname=None):
        dt = datetime.datetime.strptime(value, u'%Y-%m-%d %H:%M:%S')
        if tzname is not None:
            dt = pytz.timezone(tzname).localize(dt)
        return dt

    def _parse_date(self, value):
        dt = datetime.datetime.strptime(value, u'%Y-%m-%d')
        return dt.date()

    def _parse_time(self, value):
        dt = datetime.datetime.strptime(value, u'%H:%M:%S')
        return dt.time()

    def _check_dt(self, value, expected):
        self.assertEqual(repr(type(value)), u"<type 'datetime.datetime'>")
        self.assertEqual(value.strftime(u'%Y-%m-%d %H:%M:%S.%f %Z %z'), expected)

    def _check_date(self, value, expected):
        self.assertEqual(repr(type(value)), u"<type 'datetime.date'>")
        self.assertEqual(value.strftime(u'%Y-%m-%d'), expected)


    # local_now(), local_datetime(), local_datetime_from_local(), local_datetime_from_utc()
    def test_local_now(self):
        with mock.patch(u'django.utils.timezone.datetime', test_datetime(2014, 9, 10, 2, 20)): # in UTC
            value = local_now()
            self._check_dt(value, u'2014-09-10 04:20:00.000000 CEST +0200')

    def test_local_now_with_tz_az_tzinfo(self):
        with mock.patch(u'django.utils.timezone.datetime', test_datetime(2014, 9, 10, 2, 20)): # in UTC
            value = local_now(pytz.timezone(u'America/Montreal'))
            self._check_dt(value, u'2014-09-09 22:20:00.000000 EDT -0400')

    def test_local_now_with_tz_as_string(self):
        with mock.patch(u'django.utils.timezone.datetime', test_datetime(2014, 9, 10, 2, 20)): # in UTC
            value = local_now(u'America/Montreal')
            self._check_dt(value, u'2014-09-09 22:20:00.000000 EDT -0400')

    def test_local_datetime(self):
        value = local_datetime(self._parse_dt(u'2014-12-10 15:45:00', u'UTC'))
        self._check_dt(value, u'2014-12-10 16:45:00.000000 CET +0100')

    def test_local_datetime_with_datetime_in_another_tz(self):
        value = local_datetime(self._parse_dt(u'2014-12-20 15:45:00', u'America/Montreal'))
        self._check_dt(value, u'2014-12-20 21:45:00.000000 CET +0100')

    def test_local_datetime_with_tz_as_tzinfo(self):
        value = local_datetime(self._parse_dt(u'2014-12-10 15:45:00', u'UTC'), pytz.timezone(u'America/Montreal'))
        self._check_dt(value, u'2014-12-10 10:45:00.000000 EST -0500')

    def test_local_datetime_with_tz_as_string(self):
        value = local_datetime(self._parse_dt(u'2014-12-10 15:45:00', u'UTC'), u'America/Montreal')
        self._check_dt(value, u'2014-12-10 10:45:00.000000 EST -0500')

    def test_local_datetime_from_local(self):
        value = local_datetime_from_local(self._parse_dt(u'2014-08-15 03:45:00'))
        self._check_dt(value, u'2014-08-15 03:45:00.000000 CEST +0200')

    def test_local_datetime_from_local_with_from_tz_as_tzinfo(self):
        value = local_datetime_from_local(self._parse_dt(u'2014-08-15 03:45:00'), from_tz=pytz.timezone(u'America/Montreal'))
        self._check_dt(value, u'2014-08-15 09:45:00.000000 CEST +0200')

    def test_local_datetime_from_local_with_from_tz_as_string(self):
        value = local_datetime_from_local(self._parse_dt(u'2014-08-15 03:45:00'), from_tz=u'America/Montreal')
        self._check_dt(value, u'2014-08-15 09:45:00.000000 CEST +0200')

    def test_local_datetime_from_local_with_tz_as_tzinfo(self):
        value = local_datetime_from_local(self._parse_dt(u'2014-08-15 03:45:00'), tz=pytz.timezone(u'America/Montreal'))
        self._check_dt(value, u'2014-08-14 21:45:00.000000 EDT -0400')

    def test_local_datetime_from_local_with_tz_as_string(self):
        value = local_datetime_from_local(self._parse_dt(u'2014-08-15 03:45:00'), tz=u'America/Montreal')
        self._check_dt(value, u'2014-08-14 21:45:00.000000 EDT -0400')

    def test_local_datetime_from_local_with_both_from_tz_and_tz(self):
        value = local_datetime_from_local(self._parse_dt(u'2014-08-15 03:45:00'), from_tz=u'America/Montreal', tz=u'Europe/London')
        self._check_dt(value, u'2014-08-15 08:45:00.000000 BST +0100')

    def test_local_datetime_from_utc(self):
        value = local_datetime_from_utc(self._parse_dt(u'2014-08-15 03:45:00'))
        self._check_dt(value, u'2014-08-15 05:45:00.000000 CEST +0200')

    def test_local_datetime_from_utc_with_tz_as_tzinfo(self):
        value = local_datetime_from_utc(self._parse_dt(u'2014-08-15 03:45:00'), tz=pytz.timezone(u'America/Montreal'))
        self._check_dt(value, u'2014-08-14 23:45:00.000000 EDT -0400')

    def test_local_datetime_from_utc_with_tz_as_string(self):
        value = local_datetime_from_utc(self._parse_dt(u'2014-08-15 03:45:00'), tz=u'America/Montreal')
        self._check_dt(value, u'2014-08-14 23:45:00.000000 EDT -0400')


    # utc_now(), utc_datetime(), utc_datetime_from_local() and utc_datetime_from_utc()
    def test_utc_now(self):
        with mock.patch(u'django.utils.timezone.datetime', test_datetime(2014, 9, 10, 2, 20)): # in UTC
            value = utc_now()
            self._check_dt(value, u'2014-09-10 02:20:00.000000 UTC +0000')

    def test_utc_datetime(self):
        value = utc_datetime(self._parse_dt(u'2014-12-10 15:45:00', u'UTC'))
        self._check_dt(value, u'2014-12-10 15:45:00.000000 UTC +0000')

    def test_utc_datetime_with_datetime_in_another_tz(self):
        value = utc_datetime(self._parse_dt(u'2014-12-20 15:45:00', u'America/Montreal'))
        self._check_dt(value, u'2014-12-20 20:45:00.000000 UTC +0000')

    def test_utc_datetime_from_local(self):
        value = utc_datetime_from_local(self._parse_dt(u'2014-08-15 03:45:00'))
        self._check_dt(value, u'2014-08-15 01:45:00.000000 UTC +0000')

    def test_utc_datetime_from_local_with_from_tz_as_tzinfo(self):
        value = utc_datetime_from_local(self._parse_dt(u'2014-08-15 03:45:00'), from_tz=pytz.timezone(u'America/Montreal'))
        self._check_dt(value, u'2014-08-15 07:45:00.000000 UTC +0000')

    def test_utc_datetime_from_local_with_from_tz_as_string(self):
        value = utc_datetime_from_local(self._parse_dt(u'2014-08-15 03:45:00'), from_tz=u'America/Montreal')
        self._check_dt(value, u'2014-08-15 07:45:00.000000 UTC +0000')

    def test_utc_datetime_from_utc(self):
        value = utc_datetime_from_utc(self._parse_dt(u'2014-08-15 03:45:00'))
        self._check_dt(value, u'2014-08-15 03:45:00.000000 UTC +0000')


    # local_today(), local_date()
    def test_local_today(self):
        with mock.patch(u'django.utils.timezone.datetime', test_datetime(2014, 9, 10, 2, 20)): # in UTC
            value = local_today()
            self._check_date(value, u'2014-09-10')

    def test_local_today_with_day_change(self):
        with mock.patch(u'django.utils.timezone.datetime', test_datetime(2014, 9, 10, 23, 20)): # in UTC
            value = local_today()
            self._check_date(value, u'2014-09-11')

    def test_local_today_with_tz_as_tzinfo(self):
        with mock.patch(u'django.utils.timezone.datetime', test_datetime(2014, 9, 10, 2, 20)): # in UTC
            value = local_today(pytz.timezone(u'America/Montreal'))
            self._check_date(value, u'2014-09-09')

    def test_local_today_with_tz_as_string(self):
        with mock.patch(u'django.utils.timezone.datetime', test_datetime(2014, 9, 10, 2, 20)): # in UTC
            value = local_today(u'America/Montreal')
            self._check_date(value, u'2014-09-09')

    def test_local_date(self):
        value = local_date(self._parse_dt(u'2014-12-10 15:45:00', u'UTC'))
        self._check_date(value, u'2014-12-10')

    def test_local_date_with_day_change(self):
        value = local_date(self._parse_dt(u'2014-12-10 23:45:00', u'UTC'))
        self._check_date(value, u'2014-12-11')

    def test_local_date_with_tz_as_tzinfo(self):
        value = local_date(self._parse_dt(u'2014-12-10 15:45:00', u'UTC'), pytz.timezone(u'America/Montreal'))
        self._check_date(value, u'2014-12-10')

    def test_local_date_with_tz_as_string(self):
        value = local_date(self._parse_dt(u'2014-12-10 15:45:00', u'UTC'), u'America/Montreal')
        self._check_date(value, u'2014-12-10')


    # utc_today(), utc_date, naive_date()
    def test_utc_today(self):
        with mock.patch(u'django.utils.timezone.datetime', test_datetime(2014, 9, 10, 2, 20)): # in UTC
            value = utc_today()
            self._check_date(value, u'2014-09-10')

    def test_utc_date(self):
        value = utc_date(self._parse_dt(u'2014-12-10 15:45:00', u'Europe/Bratislava'))
        self._check_date(value, u'2014-12-10')

    def test_utc_date_with_day_change(self):
        value = utc_date(self._parse_dt(u'2014-12-10 22:45:00', u'America/Montreal'))
        self._check_date(value, u'2014-12-11')

    def test_naive_date(self):
        value = naive_date(self._parse_dt(u'2014-08-15 03:45:00'))
        self._check_date(value, u'2014-08-15')


    # All functions that use _datetime_factory() for passing datetime values.
    def test_datetime_argument_as_datetime(self):
        value = local_datetime_from_local(self._parse_dt(u'2014-08-15 03:45:00'))
        self._check_dt(value, u'2014-08-15 03:45:00.000000 CEST +0200')

    def test_datetime_argument_as_datetime_as_kwarg(self):
        value = local_datetime_from_local(datetime=self._parse_dt(u'2014-08-15 03:45:00'))
        self._check_dt(value, u'2014-08-15 03:45:00.000000 CEST +0200')

    def test_datetime_argument_as_string_datetime(self):
        value = local_datetime_from_local(u'2014-08-15 03:45:00')
        self._check_dt(value, u'2014-08-15 03:45:00.000000 CEST +0200')

    def test_datetime_argument_as_string_datetime_as_kwarg(self):
        value = local_datetime_from_local(datetime=u'2014-08-15 03:45:00')
        self._check_dt(value, u'2014-08-15 03:45:00.000000 CEST +0200')

    def test_datetime_argument_as_date_and_time(self):
        value = local_datetime_from_local(self._parse_date(u'2014-08-15'), self._parse_time('03:45:00'))
        self._check_dt(value, u'2014-08-15 03:45:00.000000 CEST +0200')

    def test_datetime_argument_as_date_and_time_as_kwargs(self):
        value = local_datetime_from_local(date=self._parse_date(u'2014-08-15'), time=self._parse_time('03:45:00'))
        self._check_dt(value, u'2014-08-15 03:45:00.000000 CEST +0200')

    def test_datetime_argument_as_date_and_string_time(self):
        value = local_datetime_from_local(self._parse_date(u'2014-08-15'), u'03:45:00')
        self._check_dt(value, u'2014-08-15 03:45:00.000000 CEST +0200')

    def test_datetime_argument_as_date_and_string_time_as_kwarg(self):
        value = local_datetime_from_local(self._parse_date(u'2014-08-15'), time=u'03:45:00')
        self._check_dt(value, u'2014-08-15 03:45:00.000000 CEST +0200')

    def test_datetime_argument_as_date_and_expanded_time(self):
        value = local_datetime_from_local(self._parse_date(u'2014-08-15'), 3, 45, 0, 123)
        self._check_dt(value, u'2014-08-15 03:45:00.000123 CEST +0200')

    def test_datetime_argument_as_date_and_expanded_time_as_kwargs(self):
        value = local_datetime_from_local(date=self._parse_date(u'2014-08-15'), hour=3, minute=45, second=0, microsecond=123)
        self._check_dt(value, u'2014-08-15 03:45:00.000123 CEST +0200')

    def test_datetime_argument_as_date_and_default_time(self):
        value = local_datetime_from_local(self._parse_date(u'2014-08-15'))
        self._check_dt(value, u'2014-08-15 00:00:00.000000 CEST +0200')

    def test_datetime_argument_as_date_and_default_time_as_kwarg(self):
        value = local_datetime_from_local(date=self._parse_date(u'2014-08-15'))
        self._check_dt(value, u'2014-08-15 00:00:00.000000 CEST +0200')

    def test_datetime_argument_as_string_date_and_time(self):
        value = local_datetime_from_local(u'2014-08-15', self._parse_time('03:45:00'))
        self._check_dt(value, u'2014-08-15 03:45:00.000000 CEST +0200')

    def test_datetime_argument_as_string_date_and_time_as_kwargs(self):
        value = local_datetime_from_local(date=u'2014-08-15', time=self._parse_time('03:45:00'))
        self._check_dt(value, u'2014-08-15 03:45:00.000000 CEST +0200')

    def test_datetime_argument_as_string_date_and_string_time(self):
        value = local_datetime_from_local(u'2014-08-15', u'03:45:00')
        self._check_dt(value, u'2014-08-15 03:45:00.000000 CEST +0200')

    def test_datetime_argument_as_string_date_and_string_time_as_kwarg(self):
        value = local_datetime_from_local(u'2014-08-15', time=u'03:45:00')
        self._check_dt(value, u'2014-08-15 03:45:00.000000 CEST +0200')

    def test_datetime_argument_as_string_date_and_expanded_time(self):
        value = local_datetime_from_local(u'2014-08-15', 3, 45, 0, 123)
        self._check_dt(value, u'2014-08-15 03:45:00.000123 CEST +0200')

    def test_datetime_argument_as_string_date_and_expanded_time_as_kwargs(self):
        value = local_datetime_from_local(date=u'2014-08-15', hour=3, minute=45, second=0, microsecond=123)
        self._check_dt(value, u'2014-08-15 03:45:00.000123 CEST +0200')

    def test_datetime_argument_as_string_date_and_default_time(self):
        value = local_datetime_from_local(u'2014-08-15')
        self._check_dt(value, u'2014-08-15 00:00:00.000000 CEST +0200')

    def test_datetime_argument_as_string_date_and_default_time_as_kwarg(self):
        value = local_datetime_from_local(date=u'2014-08-15')
        self._check_dt(value, u'2014-08-15 00:00:00.000000 CEST +0200')

    def test_datetime_argument_as_expanded_date_and_time(self):
        value = local_datetime_from_local(2014, 8, 15, self._parse_time('03:45:00'))
        self._check_dt(value, u'2014-08-15 03:45:00.000000 CEST +0200')

    def test_datetime_argument_as_expanded_date_and_time_as_kwargs(self):
        value = local_datetime_from_local(year=2014, month=8, day=15, time=self._parse_time('03:45:00'))
        self._check_dt(value, u'2014-08-15 03:45:00.000000 CEST +0200')

    def test_datetime_argument_as_expanded_date_and_string_time(self):
        value = local_datetime_from_local(2014, 8, 15, u'03:45:00')
        self._check_dt(value, u'2014-08-15 03:45:00.000000 CEST +0200')

    def test_datetime_argument_as_expanded_date_and_string_time_as_kwargs(self):
        value = local_datetime_from_local(year=2014, month=8, day=15, time=u'03:45:00.123456')
        self._check_dt(value, u'2014-08-15 03:45:00.123456 CEST +0200')

    def test_datetime_argument_as_expanded_date_and_expaded_time(self):
        value = local_datetime_from_local(2014, 8, 15, 3, 45, 0, 123)
        self._check_dt(value, u'2014-08-15 03:45:00.000123 CEST +0200')

    def test_datetime_argument_as_expanded_date_and_expaded_time_as_strings(self):
        value = local_datetime_from_local(u'2014', u'8', u'15', u'3', u'45', u'0', u'123')
        self._check_dt(value, u'2014-08-15 03:45:00.000123 CEST +0200')

    def test_datetime_argument_as_expanded_date_and_expaded_time_as_kwarg(self):
        value = local_datetime_from_local(year=2014, month=8, day=15, hour=3, minute=45, second=0, microsecond=123)
        self._check_dt(value, u'2014-08-15 03:45:00.000123 CEST +0200')

    def test_datetime_argument_as_expanded_date_and_default_time(self):
        value = local_datetime_from_local(2014, 8, 15)
        self._check_dt(value, u'2014-08-15 00:00:00.000000 CEST +0200')

    def test_datetime_argument_as_expanded_date_and_default_time_as_kwarg(self):
        value = local_datetime_from_local(year=2014, month=8, day=15)
        self._check_dt(value, u'2014-08-15 00:00:00.000000 CEST +0200')

    def test_datetime_argument_with_missing_all_arguments(self):
        with self.assertRaisesMessage(TypeError, u'Expecting argument: datetime, date or year'):
            local_datetime_from_local()

    def test_datetime_argument_with_missing_argument(self):
        with self.assertRaisesMessage(TypeError, u'Expecting argument: day'):
            local_datetime_from_local(2014, 8)

    def test_datetime_argument_with_invalid_argument(self):
        with self.assertRaisesMessage(TypeError, u'Expecting argument: day, got 3.2'):
            local_datetime_from_local(2014, 8, 3.2)

    def test_datetime_argument_with_unexpected_argument(self):
        with self.assertRaisesMessage(TypeError, u'Unexpected arguments: 2014'):
            local_datetime_from_local(self._parse_dt(u'2014-08-15 03:45:00'), 2014)

    def test_datetime_argument_with_unexpected_kw_argument(self):
        with self.assertRaisesMessage(TypeError, u'Unexpected arguments: year=2014'):
            local_datetime_from_local(self._parse_dt(u'2014-08-15 03:45:00'), year=2014)
