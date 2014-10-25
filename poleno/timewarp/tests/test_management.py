# vim: expandtab
# -*- coding: utf-8 -*-
import re
import sys
import datetime
import mock
from StringIO import StringIO

from django.core import management
from django.core.management.base import CommandError
from django.test import TestCase

from poleno.utils.misc import collect_stdout

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
        try:
            return datetime.datetime.strptime(value, u'%Y-%m-%d %H:%M:%S.%f')
        except ValueError:
            return datetime.datetime.strptime(value, u'%Y-%m-%d %H:%M:%S')

    def _call_timewarp(self, *args, **kwargs):
        with collect_stdout() as collected:
            management.call_command(u'timewarp', *args, **kwargs)
        return collected.stdout


    def test_without_arguments(self):
        with mock.patch(u'poleno.timewarp.management.commands.timewarp.timewarp') as mock_timewarp:
            self._call_timewarp(verbosity=u'0')
        expected_calls = []
        self.assertEqual(mock_timewarp.mock_calls, expected_calls)

    def test_reset(self):
        with mock.patch(u'poleno.timewarp.management.commands.timewarp.timewarp') as mock_timewarp:
            self._call_timewarp(reset=True, verbosity=u'0')
        expected_calls = [mock.call.reset()]
        self.assertEqual(mock_timewarp.mock_calls, expected_calls)

    def test_jump_yyyy_mm_dd_hh_mm_ss(self):
        with mock.patch(u'poleno.timewarp.management.commands.timewarp.timewarp') as mock_timewarp:
            self._call_timewarp(u'2014-10-03 14:40:05', verbosity=u'0')
        expected_calls = [mock.call.jump(date=self._parse_dt(u'2014-10-03 14:40:05'), speed=None)]
        self.assertEqual(mock_timewarp.mock_calls, expected_calls)

    def test_jump_yyyy_mm_dd_hh_mm(self):
        with mock.patch(u'poleno.timewarp.management.commands.timewarp.timewarp') as mock_timewarp:
            self._call_timewarp(u'2014-10-03 14:40', verbosity=u'0')
        expected_calls = [mock.call.jump(date=self._parse_dt(u'2014-10-03 14:40:00'), speed=None)]
        self.assertEqual(mock_timewarp.mock_calls, expected_calls)

    def test_jump_yyyy_mm_dd(self):
        with mock.patch(u'poleno.timewarp.management.commands.timewarp.timewarp') as mock_timewarp:
            self._call_timewarp(u'2014-10-03', verbosity=u'0')
        expected_calls = [mock.call.jump(date=self._parse_dt(u'2014-10-03 00:00:00'), speed=None)]
        self.assertEqual(mock_timewarp.mock_calls, expected_calls)

    def test_jump_yyyy_mm_dd_and_hh_mm_ss(self):
        with mock.patch(u'poleno.timewarp.management.commands.timewarp.timewarp') as mock_timewarp:
            self._call_timewarp(u'2014-10-03', u'14:40:05', verbosity=u'0')
        expected_calls = [mock.call.jump(date=self._parse_dt(u'2014-10-03 14:40:05'), speed=None)]
        self.assertEqual(mock_timewarp.mock_calls, expected_calls)

    def test_jump_invalid_date(self):
        with mock.patch(u'poleno.timewarp.management.commands.timewarp.timewarp') as mock_timewarp:
            with self.assertRaisesMessage(CommandError, u'Invalid date: "2014-10-03 :40:05".'):
                self._call_timewarp(u'2014-10-03 :40:05', verbosity=u'0')
        expected_calls = []
        self.assertEqual(mock_timewarp.mock_calls, expected_calls)

    def test_only_delta_options(self):
        with mock.patch(u'poleno.timewarp.management.commands.timewarp.timewarp') as mock_timewarp:
            self._call_timewarp(
                    year=2014, month=10, day=6, hour=10, minute=34, second=44, microsecond=300,
                    years=-3, months=-5, weeks=+1, days=+3, hours=-3, minutes=-10, seconds=+5, microseconds=+50,
                    weekday=3, verbosity=u'0')
        expected_calls = [mock.call.jump(date=self._parse_dt(u'2011-05-19 07:24:49.000350'), speed=None)]
        self.assertEqual(mock_timewarp.mock_calls, expected_calls)

    def test_delta_options_with_date(self):
        with mock.patch(u'poleno.timewarp.management.commands.timewarp.timewarp') as mock_timewarp:
            self._call_timewarp(u'2014-10-03', weekday=1, hours=10, verbosity=u'0')
        expected_calls = [mock.call.jump(date=self._parse_dt(u'2014-10-07 10:00:00'), speed=None)]
        self.assertEqual(mock_timewarp.mock_calls, expected_calls)

    def test_speedup(self):
        with mock.patch(u'poleno.timewarp.management.commands.timewarp.timewarp') as mock_timewarp:
            self._call_timewarp(speedup=4, verbosity=u'0')
        expected_date = mock.MagicMock()
        expected_date.__eq__.side_effect = lambda x: (self.assertAlmostEqual(x, datetime.datetime.now(), delta=datetime.timedelta(seconds=10)), True)[-1]
        expected_calls = [mock.call.jump(date=expected_date, speed=4)]
        self.assertEqual(mock_timewarp.mock_calls, expected_calls)

    def test_jump_with_delta_options_and_speedup_together(self):
        with mock.patch(u'poleno.timewarp.management.commands.timewarp.timewarp') as mock_timewarp:
            self._call_timewarp(u'2014-10-03', weekday=1, hours=10, speedup=4, verbosity=u'0')
        expected_calls = [mock.call.jump(date=self._parse_dt(u'2014-10-07 10:00:00'), speed=4)]
        self.assertEqual(mock_timewarp.mock_calls, expected_calls)

    def test_verbose_without_arguments(self):
        res = self._call_timewarp()
        self.assertRegexpMatches(res, re.compile(r'^Warped time: --$', flags=re.MULTILINE))
        self.assertRegexpMatches(res, re.compile(r'^Speedup: --$', flags=re.MULTILINE))

    def test_verbose_with_reset(self):
        res = self._call_timewarp(reset=True)
        self.assertRegexpMatches(res, re.compile(r'^Resetting Timewarp', flags=re.MULTILINE))
        self.assertRegexpMatches(res, re.compile(r'^Warped time: --$', flags=re.MULTILINE))
        self.assertRegexpMatches(res, re.compile(r'^Speedup: --$', flags=re.MULTILINE))

    def test_verbose_with_jump(self):
        res = self._call_timewarp(u'2014-10-03', weekday=1, hours=10, speedup=4)
        self.assertRegexpMatches(res, re.compile(r'^Jumping', flags=re.MULTILINE))
        self.assertRegexpMatches(res, re.compile(r'^Warped time: 2014-10-07 10:00:00', flags=re.MULTILINE))
        self.assertRegexpMatches(res, re.compile(r'^Speedup: 4$', flags=re.MULTILINE))
