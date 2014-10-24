# vim: expandtab
# -*- coding: utf-8 -*-
from django.http import HttpResponse, HttpResponseRedirect, HttpResponseBadRequest, HttpResponseForbidden
from django.conf.urls import patterns, url
from django.contrib.auth.models import User
from django.test import Client, TestCase
from django.test.utils import override_settings

from poleno.utils.views import require_ajax, login_required, secure_required

class SecureClient(Client):
    u"""
    In Django 1.7 you can test HTTPS requests by providing ``secure=True`` argument for testing
    client methods. Django 1.6 lacks such feature, so we path the client class a little bit to fix
    it. The patch should be deleted after migration to Django 1.7.

    Example:
        class SomeTest(TestCase):
            client_class = SecureClient

            def test_something(self):
                response = self.client.get(u'/path/', secure=True)
    """
    def request(self, **request):
        if request.pop(u'secure', False):
            request.update({
                u'SERVER_PORT': str('443'),
                u'wsgi.url_scheme': str('https'),
                })
        return super(SecureClient, self).request(**request)

class RequireAjaxTest(TestCase):
    u"""
    Tests ``@require_ajax`` decorator.
    """
    @require_ajax
    def require_ajax_view(request):
        return HttpResponse()

    urls = tuple(patterns(u'',
        url(r'^require-ajax/$', require_ajax_view),
    ))


    def test_with_ajax(self):
        u"""
        Tests that ``@require_ajax`` allows requests with ``XMLHttpRequest`` header.
        """
        response = self.client.get(u'/require-ajax/', HTTP_X_REQUESTED_WITH=u'XMLHttpRequest')
        self.assertIs(type(response), HttpResponse)
        self.assertEqual(response.status_code, 200)

    def test_without_ajax(self):
        u"""
        Tests that ``@require_ajax`` forbids requests without ``XMLHttpRequest`` header.
        """
        response = self.client.get(u'/require-ajax/')
        self.assertIs(type(response), HttpResponseBadRequest)
        self.assertEqual(response.status_code, 400)

class LoginRequiredTest(TestCase):
    u"""
    Tests ``@login_required`` decorator. Tested in both forms, with and without arguments.
    """
    @login_required
    def login_required_with_redirect_view(request):
        return HttpResponse()

    @login_required(raise_exception=True)
    def login_required_with_exception_view(request):
        return HttpResponse()

    urls = tuple(patterns(u'',
        url(r'^login-required-with-redirect/$', login_required_with_redirect_view),
        url(r'^login-required-with-exception/$', login_required_with_exception_view),
    ))


    def setUp(self):
        self.settings_override = override_settings(
            PASSWORD_HASHERS=(u'django.contrib.auth.hashers.MD5PasswordHasher',),
            )
        self.settings_override.enable()

    def tearDown(self):
        self.settings_override.disable()


    def test_anonymous_with_redirect(self):
        u"""
        Tests that ``@login_required`` redirects requests with anonymous users.
        """
        response = self.client.get(u'/login-required-with-redirect/')
        self.assertIs(type(response), HttpResponseRedirect)
        self.assertEqual(response.status_code, 302)

    def test_anonymous_with_exception(self):
        u"""
        Tests that ``@login_required(raise_exception=True)`` forbids requests with anonymous users.
        """
        response = self.client.get(u'/login-required-with-exception/')
        self.assertIs(type(response), HttpResponseForbidden)
        self.assertEqual(response.status_code, 403)

    def test_authentificated_with_redirect(self):
        u"""
        Tests that ``@login_required`` allows requests with authentificated users.
        """
        User.objects.create_user(u'john', u'lennon@thebeatles.com', u'johnpassword')
        login = self.client.login(username=u'john', password=u'johnpassword')
        self.assertTrue(login)

        response = self.client.get(u'/login-required-with-redirect/')
        self.assertIs(type(response), HttpResponse)
        self.assertEqual(response.status_code, 200)

    def test_authentificated_with_exception(self):
        u"""
        Tests that ``@login_required(raise_exception=True)`` allows requests with authentificated
        users.
        """
        User.objects.create_user(u'john', u'lennon@thebeatles.com', u'johnpassword')
        login = self.client.login(username=u'john', password=u'johnpassword')
        self.assertTrue(login)

        response = self.client.get(u'/login-required-with-exception/')
        self.assertIs(type(response), HttpResponse)
        self.assertEqual(response.status_code, 200)

class SecureRequiredTest(TestCase):
    u"""
    Tests ``@secure_required`` decorator. Tested in both forms, with and without arguments.
    """
    @secure_required
    def secure_required_with_redirect_view(request):
        return HttpResponse()

    @secure_required(raise_exception=True)
    def secure_required_with_exception_view(request):
        return HttpResponse()

    client_class = SecureClient
    urls = tuple(patterns(u'',
        url(r'^secure-required-with-redirect/$', secure_required_with_redirect_view),
        url(r'^secure-required-with-exception/$', secure_required_with_exception_view),
    ))


    def test_insecure_with_redirect(self):
        u"""
        Tests that ``@secure_required`` redirects insecure requests.
        """
        response = self.client.get(u'/secure-required-with-redirect/')
        self.assertIs(type(response), HttpResponseRedirect)
        self.assertEqual(response.status_code, 302)
        self.assertEqual(response.url, u'https://testserver/secure-required-with-redirect/')

    def test_insecure_with_exception(self):
        u"""
        Tests that ``@secure_required(raise_exception=True)`` forbids insecure requests.
        """
        response = self.client.get(u'/secure-required-with-exception/')
        self.assertIs(type(response), HttpResponseForbidden)
        self.assertEqual(response.status_code, 403)

    def test_secure_with_redirect(self):
        u"""
        Tests that ``@secure_required`` allows secure requests.
        """
        response = self.client.get(u'/secure-required-with-redirect/', secure=True)
        self.assertIs(type(response), HttpResponse)
        self.assertEqual(response.status_code, 200)

    def test_secure_with_exception(self):
        u"""
        Tests that ``@secure_required(raise_exception=True)`` allows secure requests.
        """
        response = self.client.get(u'/secure-required-with-exception/', secure=True)
        self.assertIs(type(response), HttpResponse)
        self.assertEqual(response.status_code, 200)

    def test_insecure_with_debug(self):
        u"""
        Tests that ``@secure_required`` check is disabled if ``settings.DEBUG`` is true.
        """
        with self.settings(DEBUG=True):
            response = self.client.get(u'/secure-required-with-redirect/')
            self.assertIs(type(response), HttpResponse)
            self.assertEqual(response.status_code, 200)
