# vim: expandtab
# -*- coding: utf-8 -*-
import datetime
import mock

from django.core.exceptions import ImproperlyConfigured
from django.test import TestCase

from . import workdays

class WorkdaysTest(TestCase):

    def test_undefined_holiday_set(self):
        u"""
        Function ``workdays.between()`` should raise ``ImproperlyConfigured`` exception if
        ``settings.HOLIDAYS_MODULE_PATH`` is undefined.
        """
        with mock.patch(u'poleno.workdays.workdays.settings') as settings:
            del settings.HOLIDAYS_MODULE_PATH
            with self.assertRaisesMessage(ImproperlyConfigured, workdays.SPECIFY_HOLIDAY_SET_ERROR):
                workdays.between(datetime.date(2014, 10,  9), datetime.date(2014, 12,  3))

    def test_import_holiday_set_module(self):
        u"""
        Function ``workdays.between()`` should import module with path configured in
        ``settings.HOLIDAYS_MODULE_PATH`` and use its attribute ``HOLIDAYS`` as a default holiday
        set. The default holiday set from the imported module should only be used if no
        ``holiday_set`` argument is passed to the function.
        """
        mocked_module_path = u'<mocked_holidays_molude_path>'
        def mocked_import_module(path):
            self.assertEqual(path, mocked_module_path)
            module = mock.Mock()
            module.HOLIDAYS = workdays.HolidaySet(workdays.FixedHoliday(month=10, day=10))
            return module

        with mock.patch(u'poleno.workdays.workdays.settings') as settings:
            with mock.patch(u'poleno.workdays.workdays.import_module', side_effect=mocked_import_module):
                settings.HOLIDAYS_MODULE_PATH = mocked_module_path
                # The mocked module with holiday at 2014-10-10 (friday) was imported.
                self.assertEqual(workdays.between(datetime.date(2014, 10, 8), datetime.date(2014, 10, 14)), 3) # WED -- TUE
                # The ``holiday_set`` passed as an argument has priority over the imported module.
                holidays = workdays.HolidaySet()
                self.assertEqual(workdays.between(datetime.date(2014, 10, 8), datetime.date(2014, 10, 14), holidays), 4) # WED -- TUE

    def test_empty_holiday_set(self):
        u"""
        Test weekend arithmetics with empty set of holidays. Testing empty intervals, intervals
        starting and/or ending at weekends, intervals spanning over several weekends, intervals
        several years long, and backward intervals with negative number of days.
        """
        holidays = workdays.HolidaySet()

        # Empty intreval
        self.assertEqual(workdays.between(datetime.date(2014, 10, 13), datetime.date(2014, 10, 13), holidays), 0) # MON -- MON
        self.assertEqual(workdays.between(datetime.date(2014, 10, 14), datetime.date(2014, 10, 14), holidays), 0) # TUE -- TUE
        self.assertEqual(workdays.between(datetime.date(2014, 10, 15), datetime.date(2014, 10, 15), holidays), 0) # WED -- WED
        self.assertEqual(workdays.between(datetime.date(2014, 10, 16), datetime.date(2014, 10, 16), holidays), 0) # THU -- THU
        self.assertEqual(workdays.between(datetime.date(2014, 10, 17), datetime.date(2014, 10, 17), holidays), 0) # FRI -- FRI
        self.assertEqual(workdays.between(datetime.date(2014, 10, 18), datetime.date(2014, 10, 18), holidays), 0) # SAT -- SAT
        self.assertEqual(workdays.between(datetime.date(2014, 10, 19), datetime.date(2014, 10, 19), holidays), 0) # SUN -- SUN

        # One day
        self.assertEqual(workdays.between(datetime.date(2014, 10, 13), datetime.date(2014, 10, 14), holidays), 1) # MON -- TUE
        self.assertEqual(workdays.between(datetime.date(2014, 10, 14), datetime.date(2014, 10, 15), holidays), 1) # TUE -- WED
        self.assertEqual(workdays.between(datetime.date(2014, 10, 15), datetime.date(2014, 10, 16), holidays), 1) # WED -- THU
        self.assertEqual(workdays.between(datetime.date(2014, 10, 16), datetime.date(2014, 10, 17), holidays), 1) # THU -- FRI
        self.assertEqual(workdays.between(datetime.date(2014, 10, 17), datetime.date(2014, 10, 18), holidays), 0) # FRI -- SAT
        self.assertEqual(workdays.between(datetime.date(2014, 10, 18), datetime.date(2014, 10, 19), holidays), 0) # SAT -- SUN
        self.assertEqual(workdays.between(datetime.date(2014, 10, 19), datetime.date(2014, 10, 20), holidays), 1) # SUN -- MON

        # 2 days
        self.assertEqual(workdays.between(datetime.date(2014, 10, 13), datetime.date(2014, 10, 15), holidays), 2) # MON -- WED
        self.assertEqual(workdays.between(datetime.date(2014, 10, 14), datetime.date(2014, 10, 16), holidays), 2) # TUE -- THU
        self.assertEqual(workdays.between(datetime.date(2014, 10, 15), datetime.date(2014, 10, 17), holidays), 2) # WED -- FRI
        self.assertEqual(workdays.between(datetime.date(2014, 10, 16), datetime.date(2014, 10, 18), holidays), 1) # THU -- SAT
        self.assertEqual(workdays.between(datetime.date(2014, 10, 17), datetime.date(2014, 10, 19), holidays), 0) # FRI -- SUN
        self.assertEqual(workdays.between(datetime.date(2014, 10, 18), datetime.date(2014, 10, 20), holidays), 1) # SAT -- MON
        self.assertEqual(workdays.between(datetime.date(2014, 10, 19), datetime.date(2014, 10, 21), holidays), 2) # SUN -- TUE

        # 5 days
        self.assertEqual(workdays.between(datetime.date(2014, 10, 13), datetime.date(2014, 10, 18), holidays), 4) # MON -- SAT
        self.assertEqual(workdays.between(datetime.date(2014, 10, 14), datetime.date(2014, 10, 19), holidays), 3) # TUE -- SUN
        self.assertEqual(workdays.between(datetime.date(2014, 10, 15), datetime.date(2014, 10, 20), holidays), 3) # WED -- MON
        self.assertEqual(workdays.between(datetime.date(2014, 10, 16), datetime.date(2014, 10, 21), holidays), 3) # THU -- TUE
        self.assertEqual(workdays.between(datetime.date(2014, 10, 17), datetime.date(2014, 10, 22), holidays), 3) # FRI -- WED
        self.assertEqual(workdays.between(datetime.date(2014, 10, 18), datetime.date(2014, 10, 23), holidays), 4) # SAT -- THU
        self.assertEqual(workdays.between(datetime.date(2014, 10, 19), datetime.date(2014, 10, 24), holidays), 5) # SUN -- FRI

        # One full week
        self.assertEqual(workdays.between(datetime.date(2014, 10, 13), datetime.date(2014, 10, 20), holidays), 5) # MON -- MON
        self.assertEqual(workdays.between(datetime.date(2014, 10, 14), datetime.date(2014, 10, 21), holidays), 5) # TUE -- TUE
        self.assertEqual(workdays.between(datetime.date(2014, 10, 15), datetime.date(2014, 10, 22), holidays), 5) # WED -- WED
        self.assertEqual(workdays.between(datetime.date(2014, 10, 16), datetime.date(2014, 10, 23), holidays), 5) # THU -- THU
        self.assertEqual(workdays.between(datetime.date(2014, 10, 17), datetime.date(2014, 10, 24), holidays), 5) # FRI -- FRI
        self.assertEqual(workdays.between(datetime.date(2014, 10, 18), datetime.date(2014, 10, 25), holidays), 5) # SAT -- SAT
        self.assertEqual(workdays.between(datetime.date(2014, 10, 19), datetime.date(2014, 10, 26), holidays), 5) # SUN -- SUN

        # Several full weeks
        self.assertEqual(workdays.between(datetime.date(2014, 10,  7), datetime.date(2014, 11,  4), holidays),   4*5) # TUE (41st week) -- TUE (45th week)
        self.assertEqual(workdays.between(datetime.date(2014,  3,  7), datetime.date(2014, 11, 21), holidays),  37*5) # FRI (10th week) -- FRI (47th week)
        self.assertEqual(workdays.between(datetime.date(2013,  5, 11), datetime.date(2015,  7, 18), holidays), 114*5) # SAT (19th week of 2013) -- SAT (29th week of 2015)

        # With partial weeks
        self.assertEqual(workdays.between(datetime.date(2014, 10,  9), datetime.date(2014, 12,  3), holidays),   8*5-1) # THU (41st week) -- WED (49th week)
        self.assertEqual(workdays.between(datetime.date(2014,  5, 12), datetime.date(2014, 11, 11), holidays),  26*5+1) # MON (20th week) -- TUE (46th week)
        self.assertEqual(workdays.between(datetime.date(2013, 11, 12), datetime.date(2015, 11, 15), holidays), 104*5+3) # TUE (46th week of 2013) -- SUN (46th week of 2015)

        # Backward intervals
        self.assertEqual(workdays.between(datetime.date(2014, 10, 15), datetime.date(2014, 10, 14), holidays), -1) # WED -- TUE
        self.assertEqual(workdays.between(datetime.date(2014, 10, 23), datetime.date(2014, 10, 18), holidays), -4) # THU -- SAT
        self.assertEqual(workdays.between(datetime.date(2014, 10, 26), datetime.date(2014, 10, 19), holidays), -5) # SUN -- SUN
        self.assertEqual(workdays.between(datetime.date(2014, 11, 21), datetime.date(2014,  3,  7), holidays), -37*5) # FRI (47th week) -- FRI (10th week)
        self.assertEqual(workdays.between(datetime.date(2015, 11, 15), datetime.date(2013, 11, 12), holidays), -104*5-3) # SUN (46th week of 2015) -- TUE (46th week of 2013)

    def test_nonempty_holiday_set(self):
        u"""
        Test weekend and holidays arithmetics with fixed day and easter based holidays. Testing
        holidays with/without first and/or last years of their effect, holidays colliding with
        weekends, and holidays colliding with each other.
        """
        # Note: We use the following artificial HolidaySet instead of some real holidays to make it
        # easier to test various corner cases.
        holidays = workdays.HolidaySet(
                workdays.FixedHoliday(month=10, day=8, first_year=2008),
                workdays.FixedHoliday(month=10, day=9, first_year=2012, last_year=2024),
                workdays.FixedHoliday(month=10, day=10),
                workdays.EasterHoliday(days=2), # the tuestay after Easter Sunday
                workdays.FixedHoliday(month=4, day=22), # the tuestay after Easter Sunday in 2014
                )

        # 2006-10-08 SUN: weekend
        # 2006-10-09 MON: --
        # 2006-10-10 TUE: holiday
        self.assertEqual(workdays.between(datetime.date(2006, 10, 7), datetime.date(2006, 10, 10), holidays), 1) # SAT -- TUE

        # 2007-10-08 MON: --
        # 2007-10-09 TUE: --
        # 2007-10-10 WED: holiday
        self.assertEqual(workdays.between(datetime.date(2007, 10, 7), datetime.date(2007, 10, 10), holidays), 2) # SUN -- WED

        # 2008-10-08 WED: holiday
        # 2008-10-09 THU: --
        # 2008-10-10 FRI: holiday
        self.assertEqual(workdays.between(datetime.date(2008, 10, 7), datetime.date(2008, 10, 10), holidays), 1) # TUE -- FRI

        # 2011-10-08 SAT: holiday + weekend
        # 2011-10-09 SUN: holiday + weekend
        # 2011-10-10 MON: holiday
        self.assertEqual(workdays.between(datetime.date(2011, 10, 7), datetime.date(2011, 10, 10), holidays), 0) # FRI -- MON

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
        self.assertEqual(workdays.between(datetime.date(2014, 10, 7), datetime.date(2014, 10, 12), holidays), 0) # TUE -- SUN
        self.assertEqual(workdays.between(datetime.date(2014, 10, 6), datetime.date(2014, 10, 12), holidays), 1) # MON -- SUN
        self.assertEqual(workdays.between(datetime.date(2014, 10, 7), datetime.date(2014, 10, 13), holidays), 1) # TUE -- MON
        self.assertEqual(workdays.between(datetime.date(2014, 10, 4), datetime.date(2014, 10, 14), holidays), 4) # SAT -- TUE

        # 2024-10-08 TUE: holiday
        # 2024-10-09 WED: holiday
        # 2024-10-10 THU: holiday
        self.assertEqual(workdays.between(datetime.date(2024, 10, 7), datetime.date(2024, 10, 10), holidays), 0) # MON -- THU

        # 2025-10-08 WED: holiday
        # 2025-10-09 THU: --
        # 2025-10-10 FRI: holiday
        self.assertEqual(workdays.between(datetime.date(2025, 10, 7), datetime.date(2025, 10, 10), holidays), 1) # TUE -- FRI


        # 1992-04-21 TUE: easter based holiday
        # 1992-04-22 WED: fixed day holiday
        # 1992-04-23 THU: --
        self.assertEqual(workdays.between(datetime.date(1992, 4, 20), datetime.date(1992, 4, 23), holidays), 1) # MON -- THU

        # 2014-04-21 MON: --
        # 2014-04-22 TUE: fixed day holiday + easter based holiday
        # 2014-04-23 WED: --
        self.assertEqual(workdays.between(datetime.date(2014, 4, 20), datetime.date(2014, 4, 23), holidays), 2) # SUN -- WED

        # 2019-04-21 SUN: weekend
        # 2019-04-22 MON: fixed day holiday
        # 2019-04-23 TUE: easter based holiday
        self.assertEqual(workdays.between(datetime.date(2019, 4, 20), datetime.date(2019, 4, 23), holidays), 0) # SAT -- TUE
