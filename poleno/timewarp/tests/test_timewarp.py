# vim: expandtab
# -*- coding: utf-8 -*-
import time
import datetime
import pickle

from django.utils import timezone
from django.test import TestCase

from ..timewarp import timewarp

class TimewarpTest(TestCase):
    u"""
    Tests ``Timewarp`` singleton and ``_WarpedTime`` and ``_WarpedDatetime`` fake ``time`` and
    ``datetime`` modules. Checks that the fake ``time`` and ``datetime`` modules track warped time
    and adjust all module functions correctly.
    """

    def setUp(self):
        timewarp.enable()
        timewarp.reset()

    def tearDown(self):
        timewarp.reset()


    def _parse_dt(self, value):
        dt = datetime.datetime.strptime(value, u'%Y-%m-%d %H:%M:%S')
        return dt

    def _parse_tt(self, value):
        dt = self._parse_dt(value)
        tt = dt.timetuple()
        return tt

    def _parse_ts(self, value):
        tt = self._parse_tt(value)
        ts = time.mktime(tt)
        return ts

    def _check_dt(self, value, expected):
        self.assertEqual(repr(type(value)), u"<type 'datetime.datetime'>")
        self.assertRegexpMatches(value.strftime(u'%Y-%m-%d %H:%M:%S.%f'), expected)

    def _check_ts(self, value, expected):
        dt = datetime.datetime.fromtimestamp(value)
        self._check_dt(dt, expected)

    def _check_date(self, value, expected):
        self.assertEqual(repr(type(value)), u"<type 'datetime.date'>")
        self.assertEqual(value.strftime(u'%Y-%m-%d'), expected)


    # ``_WarpedTime`` class
    def test_time_asctime(self):
        timewarp.jump(self._parse_dt(u'2014-10-03 14:40:05'))
        value = time.asctime()
        expected = timewarp._time_orig.asctime(self._parse_tt(u'2014-10-03 14:40:05'))
        self.assertEqual(value, expected)

    def test_time_asctime_with_argument(self):
        timewarp.jump(self._parse_dt(u'2014-10-03 14:40:05'))
        value = time.asctime(time.localtime(1234556))
        expected = timewarp._time_orig.asctime(timewarp._time_orig.localtime(1234556))
        self.assertEqual(value, expected)

    def test_time_ctime(self):
        timewarp.jump(self._parse_dt(u'2014-10-03 14:40:05'))
        value = time.ctime()
        expected = timewarp._time_orig.ctime(self._parse_ts(u'2014-10-03 14:40:05'))
        self.assertEqual(value, expected)

    def test_time_ctime_with_argument(self):
        timewarp.jump(self._parse_dt(u'2014-10-03 14:40:05'))
        value = time.ctime(1234556)
        expected = timewarp._time_orig.ctime(1234556)
        self.assertEqual(value, expected)

    def test_time_gmtime(self):
        timewarp.jump(self._parse_dt(u'2014-10-03 14:40:05'))
        value = time.gmtime()
        expected = timewarp._time_orig.gmtime(self._parse_ts(u'2014-10-03 14:40:05'))
        self.assertEqual(value, expected)

    def test_time_gmtime_with_argument(self):
        timewarp.jump(self._parse_dt(u'2014-10-03 14:40:05'))
        value = time.gmtime(1234556)
        expected = timewarp._time_orig.gmtime(1234556)
        self.assertEqual(value, expected)

    def test_time_localtime(self):
        timewarp.jump(self._parse_dt(u'2014-10-03 14:40:05'))
        value = time.localtime()
        expected = timewarp._time_orig.localtime(self._parse_ts(u'2014-10-03 14:40:05'))
        self.assertEqual(value, expected)

    def test_time_localtime_with_argument(self):
        timewarp.jump(self._parse_dt(u'2014-10-03 14:40:05'))
        value = time.localtime(1234556)
        expected = timewarp._time_orig.localtime(1234556)
        self.assertEqual(value, expected)

    def test_time_strftime(self):
        timewarp.jump(self._parse_dt(u'2014-10-03 14:40:05'))
        value = time.strftime(u'%c')
        expected = timewarp._time_orig.strftime(u'%c', self._parse_tt(u'2014-10-03 14:40:05'))
        self.assertEqual(value, expected)

    def test_time_strftime_with_argument(self):
        timewarp.jump(self._parse_dt(u'2014-10-03 14:40:05'))
        value = time.strftime(u'%c', time.localtime(1234556))
        expected = timewarp._time_orig.strftime(u'%c', timewarp._time_orig.localtime(1234556))
        self.assertEqual(value, expected)

    def test_time_time(self):
        timewarp.jump(self._parse_dt(u'2014-10-03 14:40:05'))
        value = time.time()
        self.assertAlmostEqual(value, 1412340005, places=0)


    # ``_WarpedDatetime`` class
    def test_datetime_date(self):
        timewarp.jump(self._parse_dt(u'2014-10-03 14:40:05'))
        value = datetime.date(2014, 10, 5)
        self._check_date(value, u'2014-10-05')

    def test_datetime_date_today(self):
        timewarp.jump(self._parse_dt(u'2014-10-03 14:40:05'))
        value = datetime.date.today()
        self._check_date(value, u'2014-10-03')

    def test_datetime_datetime(self):
        timewarp.jump(self._parse_dt(u'2014-10-03 14:40:05'))
        value = datetime.datetime(2014, 10, 5, 10, 33, 3)
        self._check_dt(value, u'2014-10-05 10:33:03.000000')

    def test_datetime_datetime_today(self):
        timewarp.jump(self._parse_dt(u'2014-10-03 14:40:05'))
        value = datetime.datetime.today()
        self._check_dt(value, u'2014-10-03 14:40:05')

    def test_datetime_datetime_now(self):
        timewarp.jump(self._parse_dt(u'2014-10-03 14:40:05'))
        value = datetime.datetime.now()
        self._check_dt(value, u'2014-10-03 14:40:05')

    def test_datetime_datetime_utcnow(self):
        timewarp.jump(self._parse_dt(u'2014-12-03 14:40:05'))
        value = time.mktime(datetime.datetime.utcnow().timetuple())
        expected = self._parse_ts(u'2014-12-03 14:40:05') + timewarp._time_orig.timezone
        self.assertEqual(value, expected)

    def test_datetime_date_is_instance(self):
        timewarp.jump(self._parse_dt(u'2014-10-03 14:40:05'))
        value = datetime.date.today()
        self.assertIsInstance(value, datetime.date)
        self.assertIsInstance(value, timewarp._datetime_orig.date)
        self.assertNotIsInstance(value, datetime.datetime)
        self.assertNotIsInstance(value, timewarp._datetime_orig.datetime)

    def test_datetime_datetime_is_instance(self):
        timewarp.jump(self._parse_dt(u'2014-10-03 14:40:05'))
        value = datetime.datetime.now()
        self.assertIsInstance(value, datetime.datetime)
        self.assertIsInstance(value, timewarp._datetime_orig.datetime)
        self.assertIsInstance(value, datetime.date)
        self.assertIsInstance(value, timewarp._datetime_orig.date)

    def test_datetime_date_is_subclass(self):
        class SubDate(timewarp._datetime_orig.date):
            pass
        self.assertTrue(issubclass(SubDate, datetime.date))
        self.assertFalse(issubclass(datetime.date, SubDate))
        self.assertTrue(issubclass(datetime.date, timewarp._datetime_orig.date))
        self.assertTrue(issubclass(timewarp._datetime_orig.date, datetime.date))

    def test_datetime_datetime_is_subclass(self):
        class SubDatetime(timewarp._datetime_orig.datetime):
            pass
        self.assertTrue(issubclass(SubDatetime, datetime.datetime))
        self.assertFalse(issubclass(datetime.datetime, SubDatetime))
        self.assertTrue(issubclass(datetime.datetime, timewarp._datetime_orig.datetime))
        self.assertTrue(issubclass(timewarp._datetime_orig.datetime, datetime.datetime))

    def test_datetime_date_pickle(self):
        timewarp.jump(self._parse_dt(u'2014-10-03 14:40:05'))
        value = datetime.date.today()
        self._check_date(value, u'2014-10-03')

        pickled = pickle.dumps(value)
        loaded = pickle.loads(pickled)
        self._check_date(loaded, u'2014-10-03')

    def test_datetime_date_pickle_after_disable(self):
        timewarp.jump(self._parse_dt(u'2014-10-03 14:40:05'))
        timewarp.disable()
        value = datetime.date(2014, 10, 5)
        pickled = pickle.dumps(value)
        loaded = pickle.loads(pickled)
        self._check_date(loaded, u'2014-10-05')

    def test_datetime_datetime_pickle(self):
        timewarp.jump(self._parse_dt(u'2014-10-03 14:40:05'))
        value = datetime.datetime.today()
        self._check_dt(value, u'2014-10-03 14:40:05')

        pickled = pickle.dumps(value)
        loaded = pickle.loads(pickled)
        self._check_dt(loaded, u'2014-10-03 14:40:05')

    def test_datetime_datetime_pickle_after_disable(self):
        timewarp.jump(self._parse_dt(u'2014-10-03 14:40:05'))
        timewarp.disable()
        value = datetime.datetime(2014, 10, 5, 10, 33, 3)
        self._check_dt(value, u'2014-10-05 10:33:03.000000')

        pickled = pickle.dumps(value)
        loaded = pickle.loads(pickled)
        self._check_dt(loaded, u'2014-10-05 10:33:03.000000')


    # ``Timewarp`` singleton
    def test_enable_and_disable(self):
        timewarp.enable()
        timewarp.enable()
        timewarp.disable()
        timewarp.disable()
        timewarp.enable()
        timewarp.enable()

    def test_properties_before_jump(self):
        self.assertEqual(timewarp.warped_from, None)
        self.assertEqual(timewarp.warped_to, None)
        self.assertEqual(timewarp.speedup, 1)
        self.assertEqual(timewarp.is_warped, False)
        self.assertAlmostEqual(timewarp.real_time, timewarp._time_orig.time(), places=2)
        self.assertAlmostEqual(timewarp.warped_time, timewarp._time_orig.time(), places=2)

    def test_properties_after_jump(self):
        before = timewarp._time_orig.time()
        timewarp.jump(self._parse_dt(u'2014-10-03 14:40:05'), speed=2)
        self.assertAlmostEqual(timewarp.warped_from, before, places=2)
        self._check_ts(timewarp.warped_to, u'2014-10-03 14:40:05.000000')
        self.assertEqual(timewarp.speedup, 2)
        self.assertTrue(timewarp.is_warped)
        self.assertAlmostEqual(timewarp.real_time, timewarp._time_orig.time(), places=2)
        self._check_ts(timewarp.warped_time, u'2014-10-03 14:40:05')

    def test_properties_after_reset(self):
        timewarp.jump(self._parse_dt(u'2014-10-03 14:40:05'), speed=2)
        timewarp.reset()
        self.assertEqual(timewarp.warped_from, None)
        self.assertEqual(timewarp.warped_to, None)
        self.assertEqual(timewarp.speedup, 1)
        self.assertEqual(timewarp.is_warped, False)
        self.assertAlmostEqual(timewarp.real_time, timewarp._time_orig.time(), places=2)
        self.assertAlmostEqual(timewarp.warped_time, timewarp._time_orig.time(), places=2)

    def test_properties_after_disable(self):
        u"""
        If timewarp is disabled, all properties looks like reseted.
        """
        timewarp.jump(self._parse_dt(u'2014-10-03 14:40:05'), speed=2)
        timewarp.disable()
        self.assertEqual(timewarp.warped_from, None)
        self.assertEqual(timewarp.warped_to, None)
        self.assertEqual(timewarp.speedup, 1)
        self.assertEqual(timewarp.is_warped, False)
        self.assertAlmostEqual(timewarp.real_time, timewarp._time_orig.time(), places=2)
        self.assertAlmostEqual(timewarp.warped_time, timewarp._time_orig.time(), places=2)

    def test_properties_after_disable_and_another_enable(self):
        u"""
        If timewarp is enabled once again, all properties get their previous values.
        """
        before = timewarp._time_orig.time()
        timewarp.jump(self._parse_dt(u'2014-10-03 14:40:05'), speed=2)
        timewarp.disable()
        timewarp.enable()
        self.assertAlmostEqual(timewarp.warped_from, before, places=2)
        self._check_ts(timewarp.warped_to, u'2014-10-03 14:40:05.000000')
        self.assertEqual(timewarp.speedup, 2)
        self.assertTrue(timewarp.is_warped)
        self.assertAlmostEqual(timewarp.real_time, timewarp._time_orig.time(), places=2)
        self._check_ts(timewarp.warped_time, u'2014-10-03 14:40:0.')

    def test_jump(self):
        timewarp.jump(self._parse_dt(u'2014-10-03 14:40:05'))
        value = datetime.datetime.now()
        self._check_dt(value, u'2014-10-03 14:40:05')

    def test_jump_speedup(self):
        u"""
        Checks that sleeping for 0.1 real seconds takes about 100 warped seconds if the time is
        running 1000 times faster than normal.
        """
        timewarp.jump(speed=1000)
        before = datetime.datetime.now()
        time.sleep(0.1)
        after = datetime.datetime.now()
        elapsed = (after-before).total_seconds()
        self.assertAlmostEqual(elapsed, 100, delta=10)

    def test_jump_slowdown(self):
        u"""
        Checks that sleeping for 0.1 real seconds takes about 100 warped microseconds if the time
        is running 1000 times slower than normal.
        """
        timewarp.jump(speed=0.001)
        before = datetime.datetime.now()
        time.sleep(0.1)
        after = datetime.datetime.now()
        elapsed = (after-before).total_seconds()
        self.assertAlmostEqual(elapsed, 0.0001, delta=0.0001)

    def test_jump_negative_speedup(self):
        u"""
        Checks that the time runs backwards if speedup is negative.
        """
        timewarp.jump(speed=-1)
        before = datetime.datetime.now()
        time.sleep(0.1)
        after = datetime.datetime.now()
        elapsed = (after-before).total_seconds()
        self.assertAlmostEqual(elapsed, -0.1, places=2)

    def test_jump_stopped_time(self):
        u"""
        Checks that the time stops if speedup is zero.
        """
        timewarp.jump(speed=0)
        before = datetime.datetime.now()
        time.sleep(0.1)
        after = datetime.datetime.now()
        elapsed = (after-before).total_seconds()
        self.assertEqual(elapsed, 0)

    def test_jump_with_disabled_timewarp_raises_error(self):
        timewarp.disable()
        with self.assertRaisesMessage(RuntimeError, u'Timewarp is disabled.'):
            timewarp.jump(self._parse_dt(u'2014-10-03 14:40:05'))

    def test_reset_returns_warped_time_back(self):
        before = datetime.datetime.now()
        timewarp.jump(self._parse_dt(u'2014-10-03 14:40:05'))
        after = datetime.datetime.now()
        elapsed = (after-before).total_seconds()
        self.assertNotAlmostEqual(elapsed, 0, places=0)

        timewarp.reset()
        after = datetime.datetime.now()
        elapsed = (after-before).total_seconds()
        self.assertAlmostEqual(elapsed, 0, places=0)
