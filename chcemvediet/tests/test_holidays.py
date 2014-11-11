# vim: expandtab
# -*- coding: utf-8 -*-
from django.test import TestCase

from poleno.workdays import workdays
from poleno.utils.date import naive_date

class HolidaysTest(TestCase):
    u"""
    Tests ``holidays.HOLIDAYS`` holidays configuration. Checks calculated numbers of workdays
    against known numbers.
    """

    def test_number_of_workdays_in_2013(self):
        result = workdays.between(naive_date(u'2012-12-31'), naive_date(u'2013-12-31'))
        self.assertEqual(result, 250)

    def test_number_of_workdays_in_2014(self):
        result = workdays.between(naive_date(u'2013-12-31'), naive_date(u'2014-12-31'))
        self.assertEqual(result, 248)

    def test_number_of_workdays_in_2015(self):
        result = workdays.between(naive_date(u'2014-12-31'), naive_date(u'2015-12-31'))
        self.assertEqual(result, 250)

    def test_number_of_workdays_in_2016(self):
        result = workdays.between(naive_date(u'2015-12-31'), naive_date(u'2016-12-31'))
        self.assertEqual(result, 250)

    def test_number_of_workdays_in_2017(self):
        result = workdays.between(naive_date(u'2016-12-31'), naive_date(u'2017-12-31'))
        self.assertEqual(result, 247)
