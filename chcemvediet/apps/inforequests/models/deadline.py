# vim: expandtab
# -*- coding: utf-8 -*-
import datetime

from django.utils.functional import cached_property

from poleno.workdays import workdays
from poleno.utils.date import local_today
from poleno.utils.misc import Bunch, FormatMixin


class Deadline(FormatMixin, object):

    TYPES = Bunch(
            OBLIGEE_DEADLINE = 1,
            APPLICANT_DEADLINE = 2,
            )

    UNITS = Bunch(
            CALENDAR_DAYS = 1,
            WORKDAYS = 2,
            )

    def __init__(self, type, base_date, value, unit, snooze):
        self.type = type
        self.base_date = base_date
        self.value = value
        self.unit = unit
        self._snooze = snooze
        self._today = local_today()

    @property
    def is_obligee_deadline(self):
        return self.type == self.TYPES.OBLIGEE_DEADLINE

    @property
    def is_applicant_deadline(self):
        return self.type == self.TYPES.APPLICANT_DEADLINE

    @property
    def is_in_calendar_days(self):
        return self.unit == self.UNITS.CALENDAR_DAYS

    @property
    def is_in_workdays(self):
        return self.unit == self.UNITS.WORKDAYS

    @cached_property
    def deadline_date(self):
        if self.is_in_calendar_days:
            return self.base_date + datetime.timedelta(days=self.value)
        else:
            return workdays.advance(self.base_date, self.value)

    @cached_property
    def calendar_days_passed(self):
        return self.calendar_days_passed_at(self._today)

    def calendar_days_passed_at(self, at):
        return (at - self.base_date).days

    @cached_property
    def workdays_passed(self):
        return self.workdays_passed_at(self._today)

    def workdays_passed_at(self, at):
        return workdays.between(self.base_date, at)

    @cached_property
    def calendar_days_remaining(self):
        return self.calendar_days_remaining_at(self._today)

    def calendar_days_remaining_at(self, at):
        return (self.deadline_date - at).days

    @cached_property
    def workdays_remaining(self):
        return self.workdays_remaining_at(self._today)

    def workdays_remaining_at(self, at):
        return workdays.between(at, self.deadline_date)

    @cached_property
    def calendar_days_behind(self):
        return -self.calendar_days_remaining

    def calendar_days_behind_at(self, at):
        return -self.calendar_days_remaining_at(at)

    @cached_property
    def workdays_behind(self):
        return -self.workdays_remaining

    def workdays_behind_at(self, at):
        return -self.workdays_remaining_at(at)

    @cached_property
    def is_deadline_missed(self):
        return self.is_deadline_missed_at(self._today)

    def is_deadline_missed_at(self, at):
        return self.deadline_date < at

    @cached_property
    def snooze_date(self):
        return max(self._snooze, self.deadline_date) if self._snooze else self.deadline_date

    @cached_property
    def is_snoozed(self):
        return self.snooze_date > self.deadline_date

    @cached_property
    def snooze_in_calendar_days(self):
        return self.calendar_days_behind_at(self.snooze_date)

    @cached_property
    def snooze_in_workdays(self):
        return self.workdays_behind_at(self.snooze_date)

    @cached_property
    def snooze_calendar_days_remaining(self):
        return self.snooze_calendar_days_remaining_at(self._today)

    def snooze_calendar_days_remaining_at(self, at):
        return (self.snooze_date - at).days

    @cached_property
    def snooze_workdays_remaining(self):
        return self.snooze_workdays_remaining_at(self._today)

    def snooze_workdays_remaining_at(self, at):
        return workdays.between(at, self.snooze_date)

    @cached_property
    def snooze_calendar_days_behind(self):
        return -self.snooze_calendar_days_remaining

    def snooze_calendar_days_behind_at(self, at):
        return -self.snooze_calendar_days_remaining_at(at)

    @cached_property
    def snooze_workdays_behind(self):
        return -self.snooze_workdays_remaining

    def snooze_workdays_behind_at(self, at):
        return -self.snooze_workdays_remaining_at(at)

    @cached_property
    def is_snooze_missed(self):
        return self.is_snooze_missed_at(self._today)

    def is_snooze_missed_at(self, at):
        return self.snooze_date < at

    def __str__(self):
        return u'{} {} for {} since {}{}'.format(
                self.value,
                u'CD' if self.is_in_calendar_days else u'WD',
                u'Applicant' if self.is_applicant_deadline else u'Obligee',
                self.base_date,
                u' +{0} CD'.format(self.snooze_in_calendar_days)
                    if self.snooze_date != self.deadline_date else u'',
                )
