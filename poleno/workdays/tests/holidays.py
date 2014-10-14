# vim: expandtab
# -*- coding: utf-8 -*-
from poleno.workdays.workdays import HolidaySet, FixedHoliday

HOLIDAYS = HolidaySet(
        FixedHoliday(month=10, day=10),
        )
