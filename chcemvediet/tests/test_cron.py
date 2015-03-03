# vim: expandtab
# -*- coding: utf-8 -*-
from django.contrib.auth.models import User
from django.contrib.sessions.models import Session
from django.test import TestCase
from django.test.utils import override_settings

from poleno.timewarp import timewarp
from poleno.utils.date import utc_datetime_from_local

from ..cron import clear_expired_sessions

class ClearExpiredSessionsCronjobTest(TestCase):
    u"""
    Tests ``chcemvediet.cron.clear_expired_sessions`` cron job.
    """

    def _pre_setup(self):
        super(ClearExpiredSessionsCronjobTest, self)._pre_setup()
        timewarp.enable()
        timewarp.reset()
        self.settings_override = override_settings(
            PASSWORD_HASHERS=(u'django.contrib.auth.hashers.MD5PasswordHasher',),
            )
        self.settings_override.enable()

    def _post_teardown(self):
        self.settings_override.disable()
        timewarp.reset()
        super(ClearExpiredSessionsCronjobTest, self)._post_teardown()

    def test_sessions_older_than_two_weeks_are_cleared(self):
        timewarp.jump(utc_datetime_from_local(u'2014-10-01 09:30:00'))
        user = User.objects.create_user(u'aaa', password=u'ppp')
        self.client.login(username=user.username, password=u'ppp')

        timewarp.jump(utc_datetime_from_local(u'2014-10-16 09:30:00'))
        self.assertTrue(Session.objects.exists())
        clear_expired_sessions().do()
        self.assertFalse(Session.objects.exists())

    def test_sessions_newer_than_two_weeks_are_kept(self):
        timewarp.jump(utc_datetime_from_local(u'2014-10-01 09:30:00'))
        user = User.objects.create_user(u'aaa', password=u'ppp')
        self.client.login(username=user.username, password=u'ppp')

        timewarp.jump(utc_datetime_from_local(u'2014-10-14 09:30:00'))
        self.assertTrue(Session.objects.exists())
        clear_expired_sessions().do()
        self.assertTrue(Session.objects.exists())
