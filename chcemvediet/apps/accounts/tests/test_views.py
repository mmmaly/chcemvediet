# vim: expandtab
# -*- coding: utf-8 -*-
from django.core.urlresolvers import reverse
from django.http import HttpResponse
from django.contrib.auth.models import User
from django.utils.http import urlencode
from django.test import TestCase

from . import AccountsTestCaseMixin

class ProfileViewTest(AccountsTestCaseMixin, TestCase):
    u"""
    Tests ``profile()`` view.
    """

    def setUp(self):
        self.user = User.objects.create_user(u'john', u'lennon@thebeatles.com', u'johnpassword')


    def test_head_method_is_allowed(self):
        response = self.client.head(reverse(u'accounts:profile'))
        self.assertEqual(response.status_code, 302)

    def test_get_method_is_allowed(self):
        response = self.client.get(reverse(u'accounts:profile'))
        self.assertEqual(response.status_code, 302)

    def test_post_method_is_not_allowed(self):
        response = self.client.post(reverse(u'accounts:profile'))
        self.assertEqual(response.status_code, 405)
        self.assertEqual(response[u'Allow'], u'HEAD, GET')

    def test_anonymous_user_is_redirected(self):
        response = self.client.get(reverse(u'accounts:profile'), follow=True)
        expected_url = reverse(u'account_login') + u'?' + urlencode({u'next': reverse(u'accounts:profile')})
        self.assertRedirects(response, expected_url)

    def test_authenticated_user_gets_his_profile(self):
        self.client.login(username=u'john', password=u'johnpassword')
        response = self.client.get(reverse(u'accounts:profile'))
        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, u'accounts/profile.html')
        self.assertEqual(response.context[u'user'], self.user)
