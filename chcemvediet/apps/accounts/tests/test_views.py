# vim: expandtab
# -*- coding: utf-8 -*-
from django.core.urlresolvers import reverse
from django.http import HttpResponse
from django.contrib.auth.models import User
from django.utils.http import urlencode
from django.test import TestCase

from poleno.utils.test import ViewTestCaseMixin

from . import AccountsTestCaseMixin

class ProfileViewTest(AccountsTestCaseMixin, ViewTestCaseMixin, TestCase):
    u"""
    Tests ``profile()`` view registered as "accounts:profile".
    """

    def setUp(self):
        self.user = User.objects.create_user(u'john', u'lennon@thebeatles.com', u'johnpassword')


    def test_allowed_http_methods(self):
        allowed = [u'HEAD', u'GET']
        self.assert_allowed_http_methods(allowed, reverse(u'accounts:profile'))

    def test_anonymous_user_is_redirected(self):
        self.assert_anonymous_user_is_redirected(reverse(u'accounts:profile'))

    def test_authenticated_user_gets_his_profile(self):
        self.client.login(username=u'john', password=u'johnpassword')
        response = self.client.get(reverse(u'accounts:profile'))
        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, u'accounts/profile.html')
        self.assertEqual(response.context[u'user'], self.user)
