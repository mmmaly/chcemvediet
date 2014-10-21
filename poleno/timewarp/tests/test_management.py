# vim: expandtab
# -*- coding: utf-8 -*-
import sys
import datetime
from StringIO import StringIO

from django.core import management
from django.core.management.base import CommandError
from django.test import TestCase

from ..timewarp import timewarp

class TimewarpManagementTest(TestCase):
    u"""
    Tests timewarp management command ``timewarp``. Only checks if the management command sets all
    ``timewarp`` attributes correctly. Timewarp functionality is tested in ``test_timewarp.py``.
    """

    def setUp(self):
        timewarp.enable()
        timewarp.reset()

    def tearDown(self):
        timewarp.reset()


    def _parse_dt(self, value):
        dt = datetime.datetime.strptime(value, u'%Y-%m-%d %H:%M:%S')
        return dt

    def _check_dt(self, value, expected):
        self.assertEqual(repr(type(value)), u"<type 'datetime.datetime'>")
        self.assertRegexpMatches(value.strftime(u'%Y-%m-%d %H:%M:%S.%f'), expected)

    def _check_ts(self, value, expected):
        dt = datetime.datetime.fromtimestamp(value)
        self._check_dt(dt, expected)


    def _call_timewarp(self, *args, **kwargs):
        try:
            orig_stdout = sys.stdout
            sys.stdout = StringIO()
            management.call_command(u'timewarp', *args, **kwargs)
            sys.stdout.seek(0)
            return sys.stdout.read()
        finally:
            sys.stdout = orig_stdout


    def test_without_arguments(self):
        self._call_timewarp()
        self.assertFalse(timewarp.is_warped)

    def test_reset(self):
        timewarp.jump(self._parse_dt(u'2014-10-03 14:40:05'), speed=2)
        self.assertTrue(timewarp.is_warped)
        self._call_timewarp(reset=True)
        self.assertFalse(timewarp.is_warped)

    def test_jump_yyyy_mm_dd_hh_mm_ss(self):
        self._call_timewarp(u'2014-10-03 14:40:05')
        self._check_ts(timewarp.warped_to, u'2014-10-03 14:40:05.000000')

    def test_jump_yyyy_mm_dd_hh_mm(self):
        self._call_timewarp(u'2014-10-03 14:40')
        self._check_ts(timewarp.warped_to, u'2014-10-03 14:40:00.000000')

    def test_jump_yyyy_mm_dd(self):
        self._call_timewarp(u'2014-10-03')
        self._check_ts(timewarp.warped_to, u'2014-10-03 00:00:00.000000')

    def test_jump_yyyy_mm_dd_and_hh_mm_ss(self):
        self._call_timewarp(u'2014-10-03', u'14:40:05')
        self._check_ts(timewarp.warped_to, u'2014-10-03 14:40:05.000000')

    def test_jump_invalid_date(self):
        with self.assertRaisesMessage(CommandError, u'Invalid date: "2014-10-03 :40:05".'):
            self._call_timewarp(u'2014-10-03 :40:05')

    def test_only_delta_options(self):
        self._call_timewarp(
                year=2014, month=10, day=6, hour=10, minute=34, second=44,
                years=-3, months=-5, weeks=+1, days=+3, hours=-3, minutes=-10, seconds=+5,
                weekday=3)
        self._check_ts(timewarp.warped_to, u'2011-05-19 07:24:49.000000')

    def test_delta_options_with_date(self):
        self._call_timewarp(u'2014-10-03', weekday=1, hours=10)
        self._check_ts(timewarp.warped_to, u'2014-10-07 10:00:00.000000')

    def test_speedup(self):
        self._call_timewarp(speedup=4)
        self.assertEqual(timewarp.speedup, 4)

    def test_jump_with_delta_options_and_speedup_together(self):
        self._call_timewarp(u'2014-10-03', weekday=1, hours=10, speedup=4)
        self._check_ts(timewarp.warped_to, u'2014-10-07 10:00:00.000000')
        self.assertEqual(timewarp.speedup, 4)
