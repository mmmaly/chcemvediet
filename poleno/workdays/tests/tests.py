# vim: expandtab
# -*- coding: utf-8 -*-
import mock
from datetime import date

from django.core.exceptions import ImproperlyConfigured
from django.test import TestCase

from poleno.workdays.workdays import between, HolidaySet, FixedHoliday, EasterHoliday, SPECIFY_HOLIDAY_SET_ERROR

class WorkdaysTest(TestCase):
    u"""
    Tests ``between()`` function and ``Holiday``, ``FixedHoliday``, ``EasterHoliday`` and
    ``HolidaySet`` classes.
    """

    def test_undefined_holiday_set(self):
        u"""
        Function ``between()`` should raise ``ImproperlyConfigured`` exception if
        ``settings.HOLIDAYS_MODULE_PATH`` is undefined.
        """
        with mock.patch(u'poleno.workdays.workdays.settings') as settings:
            del settings.HOLIDAYS_MODULE_PATH
            with self.assertRaisesMessage(ImproperlyConfigured, SPECIFY_HOLIDAY_SET_ERROR):
                between(date(2014, 10,  9), date(2014, 12,  3))

    def test_import_holiday_set_module(self):
        u"""
        Function ``between()`` should import module with path configured in
        ``settings.HOLIDAYS_MODULE_PATH`` and use its attribute ``HOLIDAYS`` as a default holiday
        set. The default holiday set from the imported module should only be used if no
        ``holiday_set`` argument is passed to the function.
        """
        with mock.patch(u'poleno.workdays.workdays.settings') as settings:
            settings.HOLIDAYS_MODULE_PATH = u'poleno.workdays.tests.holidays'
            # The mock module with holiday at 2014-10-10 (FRI) was imported.
            self.assertEqual(between(date(2014, 10, 8), date(2014, 10, 14)), 3) # WED -- TUE
            # The ``holiday_set`` passed as an argument has priority over the imported module.
            holidays = HolidaySet()
            self.assertEqual(between(date(2014, 10, 8), date(2014, 10, 14), holidays), 4) # WED -- TUE

    def test_empty_holiday_set(self):
        u"""
        Test weekend arithmetics with empty set of holidays. Testing empty intervals, intervals
        starting and/or ending at weekends, intervals spanning over several weekends, intervals
        several years long, and backward intervals with negative number of days.
        """
        holidays = HolidaySet()

        # Empty intreval
        self.assertEqual(between(date(2014, 10, 13), date(2014, 10, 13), holidays), 0) # MON -- MON
        self.assertEqual(between(date(2014, 10, 14), date(2014, 10, 14), holidays), 0) # TUE -- TUE
        self.assertEqual(between(date(2014, 10, 15), date(2014, 10, 15), holidays), 0) # WED -- WED
        self.assertEqual(between(date(2014, 10, 16), date(2014, 10, 16), holidays), 0) # THU -- THU
        self.assertEqual(between(date(2014, 10, 17), date(2014, 10, 17), holidays), 0) # FRI -- FRI
        self.assertEqual(between(date(2014, 10, 18), date(2014, 10, 18), holidays), 0) # SAT -- SAT
        self.assertEqual(between(date(2014, 10, 19), date(2014, 10, 19), holidays), 0) # SUN -- SUN

        # One day
        self.assertEqual(between(date(2014, 10, 13), date(2014, 10, 14), holidays), 1) # MON -- TUE
        self.assertEqual(between(date(2014, 10, 14), date(2014, 10, 15), holidays), 1) # TUE -- WED
        self.assertEqual(between(date(2014, 10, 15), date(2014, 10, 16), holidays), 1) # WED -- THU
        self.assertEqual(between(date(2014, 10, 16), date(2014, 10, 17), holidays), 1) # THU -- FRI
        self.assertEqual(between(date(2014, 10, 17), date(2014, 10, 18), holidays), 0) # FRI -- SAT
        self.assertEqual(between(date(2014, 10, 18), date(2014, 10, 19), holidays), 0) # SAT -- SUN
        self.assertEqual(between(date(2014, 10, 19), date(2014, 10, 20), holidays), 1) # SUN -- MON

        # 2 days
        self.assertEqual(between(date(2014, 10, 13), date(2014, 10, 15), holidays), 2) # MON -- WED
        self.assertEqual(between(date(2014, 10, 14), date(2014, 10, 16), holidays), 2) # TUE -- THU
        self.assertEqual(between(date(2014, 10, 15), date(2014, 10, 17), holidays), 2) # WED -- FRI
        self.assertEqual(between(date(2014, 10, 16), date(2014, 10, 18), holidays), 1) # THU -- SAT
        self.assertEqual(between(date(2014, 10, 17), date(2014, 10, 19), holidays), 0) # FRI -- SUN
        self.assertEqual(between(date(2014, 10, 18), date(2014, 10, 20), holidays), 1) # SAT -- MON
        self.assertEqual(between(date(2014, 10, 19), date(2014, 10, 21), holidays), 2) # SUN -- TUE

        # 5 days
        self.assertEqual(between(date(2014, 10, 13), date(2014, 10, 18), holidays), 4) # MON -- SAT
        self.assertEqual(between(date(2014, 10, 14), date(2014, 10, 19), holidays), 3) # TUE -- SUN
        self.assertEqual(between(date(2014, 10, 15), date(2014, 10, 20), holidays), 3) # WED -- MON
        self.assertEqual(between(date(2014, 10, 16), date(2014, 10, 21), holidays), 3) # THU -- TUE
        self.assertEqual(between(date(2014, 10, 17), date(2014, 10, 22), holidays), 3) # FRI -- WED
        self.assertEqual(between(date(2014, 10, 18), date(2014, 10, 23), holidays), 4) # SAT -- THU
        self.assertEqual(between(date(2014, 10, 19), date(2014, 10, 24), holidays), 5) # SUN -- FRI

        # One full week
        self.assertEqual(between(date(2014, 10, 13), date(2014, 10, 20), holidays), 5) # MON -- MON
        self.assertEqual(between(date(2014, 10, 14), date(2014, 10, 21), holidays), 5) # TUE -- TUE
        self.assertEqual(between(date(2014, 10, 15), date(2014, 10, 22), holidays), 5) # WED -- WED
        self.assertEqual(between(date(2014, 10, 16), date(2014, 10, 23), holidays), 5) # THU -- THU
        self.assertEqual(between(date(2014, 10, 17), date(2014, 10, 24), holidays), 5) # FRI -- FRI
        self.assertEqual(between(date(2014, 10, 18), date(2014, 10, 25), holidays), 5) # SAT -- SAT
        self.assertEqual(between(date(2014, 10, 19), date(2014, 10, 26), holidays), 5) # SUN -- SUN

        # Several full weeks
        self.assertEqual(between(date(2014, 10,  7), date(2014, 11,  4), holidays),   4*5) # TUE (41st week) -- TUE (45th week)
        self.assertEqual(between(date(2014,  3,  7), date(2014, 11, 21), holidays),  37*5) # FRI (10th week) -- FRI (47th week)
        self.assertEqual(between(date(2013,  5, 11), date(2015,  7, 18), holidays), 114*5) # SAT (19th week of 2013) -- SAT (29th week of 2015)

        # With partial weeks
        self.assertEqual(between(date(2014, 10,  9), date(2014, 12,  3), holidays),   8*5-1) # THU (41st week) -- WED (49th week)
        self.assertEqual(between(date(2014,  5, 12), date(2014, 11, 11), holidays),  26*5+1) # MON (20th week) -- TUE (46th week)
        self.assertEqual(between(date(2013, 11, 12), date(2015, 11, 15), holidays), 104*5+3) # TUE (46th week of 2013) -- SUN (46th week of 2015)

        # Backward intervals
        self.assertEqual(between(date(2014, 10, 15), date(2014, 10, 14), holidays), -1) # WED -- TUE
        self.assertEqual(between(date(2014, 10, 23), date(2014, 10, 18), holidays), -4) # THU -- SAT
        self.assertEqual(between(date(2014, 10, 26), date(2014, 10, 19), holidays), -5) # SUN -- SUN
        self.assertEqual(between(date(2014, 11, 21), date(2014,  3,  7), holidays), -37*5) # FRI (47th week) -- FRI (10th week)
        self.assertEqual(between(date(2015, 11, 15), date(2013, 11, 12), holidays), -104*5-3) # SUN (46th week of 2015) -- TUE (46th week of 2013)

    def test_nonempty_holiday_set(self):
        u"""
        Test weekend and holidays arithmetics with fixed day and easter based holidays. Testing
        holidays with/without first and/or last years of their effect, holidays colliding with
        weekends, and holidays colliding with each other.
        """
        # Note: We use the following artificial HolidaySet instead of some real holidays to make it
        # easier to test various corner cases.
        holidays = HolidaySet(
                FixedHoliday(month=10, day=8, first_year=2008),
                FixedHoliday(month=10, day=9, first_year=2012, last_year=2024),
                FixedHoliday(month=10, day=10),
                EasterHoliday(days=2), # the tuestay after Easter Sunday
                FixedHoliday(month=4, day=22), # the tuestay after Easter Sunday in 2014
                )

        # 2006-10-08 SUN: weekend
        # 2006-10-09 MON: --
        # 2006-10-10 TUE: holiday
        self.assertEqual(between(date(2006, 10, 7), date(2006, 10, 10), holidays), 1) # SAT -- TUE

        # 2007-10-08 MON: --
        # 2007-10-09 TUE: --
        # 2007-10-10 WED: holiday
        self.assertEqual(between(date(2007, 10, 7), date(2007, 10, 10), holidays), 2) # SUN -- WED

        # 2008-10-08 WED: holiday
        # 2008-10-09 THU: --
        # 2008-10-10 FRI: holiday
        self.assertEqual(between(date(2008, 10, 7), date(2008, 10, 10), holidays), 1) # TUE -- FRI

        # 2011-10-08 SAT: holiday + weekend
        # 2011-10-09 SUN: holiday + weekend
        # 2011-10-10 MON: holiday
        self.assertEqual(between(date(2011, 10, 7), date(2011, 10, 10), holidays), 0) # FRI -- MON

        # 2014-10-05 SUN: weekend
        # 2014-10-06 MON: --
        # 2014-10-07 TUE: --
        # 2014-10-08 WED: holiday
        # 2014-10-09 THU: holiday
        # 2014-10-10 FRI: holiday
        # 2014-10-11 SAT: weekend
        # 2014-10-12 SUN: weekend
        # 2014-10-13 MON: --
        # 2014-10-14 TUE: --
        self.assertEqual(between(date(2014, 10, 7), date(2014, 10, 12), holidays), 0) # TUE -- SUN
        self.assertEqual(between(date(2014, 10, 6), date(2014, 10, 12), holidays), 1) # MON -- SUN
        self.assertEqual(between(date(2014, 10, 7), date(2014, 10, 13), holidays), 1) # TUE -- MON
        self.assertEqual(between(date(2014, 10, 4), date(2014, 10, 14), holidays), 4) # SAT -- TUE

        # 2024-10-08 TUE: holiday
        # 2024-10-09 WED: holiday
        # 2024-10-10 THU: holiday
        self.assertEqual(between(date(2024, 10, 7), date(2024, 10, 10), holidays), 0) # MON -- THU

        # 2025-10-08 WED: holiday
        # 2025-10-09 THU: --
        # 2025-10-10 FRI: holiday
        self.assertEqual(between(date(2025, 10, 7), date(2025, 10, 10), holidays), 1) # TUE -- FRI


        # 1992-04-21 TUE: easter based holiday
        # 1992-04-22 WED: fixed day holiday
        # 1992-04-23 THU: --
        self.assertEqual(between(date(1992, 4, 20), date(1992, 4, 23), holidays), 1) # MON -- THU

        # 2014-04-21 MON: --
        # 2014-04-22 TUE: fixed day holiday + easter based holiday
        # 2014-04-23 WED: --
        self.assertEqual(between(date(2014, 4, 20), date(2014, 4, 23), holidays), 2) # SUN -- WED

        # 2019-04-21 SUN: weekend
        # 2019-04-22 MON: fixed day holiday
        # 2019-04-23 TUE: easter based holiday
        self.assertEqual(between(date(2019, 4, 20), date(2019, 4, 23), holidays), 0) # SAT -- TUE
