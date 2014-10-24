# vim: expandtab
# -*- coding: utf-8 -*-
import datetime

from django.core.urlresolvers import reverse
from django.http import HttpResponse, HttpResponseRedirect
from django.contrib.auth.models import User
from django.test import TestCase
from django.test.utils import override_settings

from ..timewarp import timewarp

class TimewarpAdminTest(TestCase):
    u"""
    Tests timewarp admin views. Only checks if the views retrieve and update ``timewarp``
    attributes correctly.  Timewarp functionality is tested in ``test_timewarp.py``.
    """

    def setUp(self):
        timewarp.enable()
        timewarp.reset()

        self.settings_override = override_settings(
            PASSWORD_HASHERS=(u'django.contrib.auth.hashers.MD5PasswordHasher',),
            )
        self.settings_override.enable()

        self.admin = User.objects.create_superuser(username=u'admin', email=u'admin@example.com', password=u'top_secret')
        self.client.login(username=u'admin', password=u'top_secret')

    def tearDown(self):
        timewarp.reset()

        self.settings_override.disable()


    def _parse_dt(self, value):
        dt = datetime.datetime.strptime(value, u'%Y-%m-%d %H:%M:%S')
        return dt

    def _check_dt(self, value, expected):
        self.assertEqual(repr(type(value)), u"<type 'datetime.datetime'>")
        self.assertRegexpMatches(value.strftime(u'%Y-%m-%d %H:%M:%S.%f'), expected)

    def _check_ts(self, value, expected):
        dt = datetime.datetime.fromtimestamp(value)
        self._check_dt(dt, expected)

    def _check_response(self, response, template, klass=HttpResponse, status_code=200):
        self.assertIs(type(response), klass)
        self.assertEqual(response.status_code, status_code)
        self.assertTemplateUsed(response, template)


    def test_head(self):
        response = self.client.head(reverse(u'admin:timewarp'))
        self._check_response(response, u'timewarp/timewarp.html')

    def test_get(self):
        response = self.client.get(reverse(u'admin:timewarp'))
        self._check_response(response, u'timewarp/timewarp.html')

    def test_post_reset(self):
        timewarp.jump(self._parse_dt(u'2014-10-03 14:40:05'), speed=2)
        self.assertTrue(timewarp.is_warped)
        response = self.client.post(reverse(u'admin:timewarp'), data={u'button': u'reset'}, follow=True)
        self.assertRedirects(response, reverse(u'admin:timewarp'))
        self._check_response(response, u'timewarp/timewarp.html')
        self.assertFalse(timewarp.is_warped)

    def test_post_jump_with_jumpto_and_speedup(self):
        response = self.client.post(reverse(u'admin:timewarp'), data={u'button': u'jump', u'jumpto': u'2014-10-03', u'speedup': 3}, follow=True)
        self.assertRedirects(response, reverse(u'admin:timewarp'))
        self._check_response(response, u'timewarp/timewarp.html')
        self._check_ts(timewarp.warped_to, u'2014-10-03 00:00:00.000000')
        self.assertEqual(timewarp.speedup, 3)

    def test_post_jump_with_speedup_only(self):
        response = self.client.post(reverse(u'admin:timewarp'), data={u'button': u'jump', u'speedup': 3}, follow=True)
        self.assertRedirects(response, reverse(u'admin:timewarp'))
        self._check_response(response, u'timewarp/timewarp.html')
        self.assertAlmostEqual(timewarp.warped_from, timewarp.warped_to, places=2)
        self.assertEqual(timewarp.speedup, 3)

    def test_post_jump_without_jumpto_nor_speedup(self):
        response = self.client.post(reverse(u'admin:timewarp'), data={u'button': u'jump'}, follow=True)
        self.assertRedirects(response, reverse(u'admin:timewarp'))
        self._check_response(response, u'timewarp/timewarp.html')
        self.assertFalse(timewarp.is_warped)

    def test_post_jump_with_invalid_jumpto(self):
        response = self.client.post(reverse(u'admin:timewarp'), data={u'button': u'jump', u'jumpto': u'2014-10-xx'}, follow=True)
        self._check_response(response, u'timewarp/timewarp.html')
        self.assertFormError(response, u'form', u'jumpto', u'Enter a valid date/time.')
        self.assertFalse(timewarp.is_warped)

    def test_post_jump_with_invalid_speedup(self):
        response = self.client.post(reverse(u'admin:timewarp'), data={u'button': u'jump', u'speedup': u'invalid'}, follow=True)
        self._check_response(response, u'timewarp/timewarp.html')
        self.assertFormError(response, u'form', u'speedup', u'Enter a number.')
        self.assertFalse(timewarp.is_warped)

    def test_post_with_invalid_button(self):
        response = self.client.post(reverse(u'admin:timewarp'), data={u'button': u'invalid'}, follow=True)
        self._check_response(response, u'timewarp/timewarp.html')
        self.assertFalse(timewarp.is_warped)
