# vim: expandtab
# -*- coding: utf-8 -*-
import mock
import contextlib
import importlib
import logging

from django.utils.http import urlencode
from django.test import TestCase

from poleno.utils.urls import reverse


@contextlib.contextmanager
def patch_logger(logger_name, log_level):
    u"""
    Replacement for ``django.test.utils.patch_logger`` removed in Django 3.0. Replaces the
    ``log_level`` method of the named logger and collects the formatted messages in the yielded
    list. Works even when logging is disabled by the test runner.
    """
    calls = []
    def replacement(msg, *args, **kwargs):
        calls.append(msg % args if args else msg)
    logger = logging.getLogger(logger_name)
    original = getattr(logger, log_level)
    setattr(logger, log_level, replacement)
    try:
        yield calls
    finally:
        setattr(logger, log_level, original)

@contextlib.contextmanager
def override_signals(*signals):
    u"""
    Locally overrides django signal receivers. Usefull for testing signals wihtout concern about
    side effects of other registered signal receivers, It disables all registered listeners and
    lets you register your own listeners within a ``with`` statement. After the ``with`` statement
    all your new listeners are discarted and original signal receivers are restored.

    Example:
        message_sent.connect(original_receiver)
        with override_signals(message_sent, message_received):
            message_sent.connect(new_receiver)
            message_sent.send() # only ``new_receiver`` receives it
        message_sent.send() # only ``original_receiver`` receives it
    """
    original_receivers = {}
    for signal in signals:
        original_receivers[signal] = signal.receivers
        signal.receivers = []
        signal.sender_receivers_cache.clear()
    try:
        yield
    finally:
        for signal in signals:
            signal.receivers = original_receivers[signal]
            signal.sender_receivers_cache.clear()

@contextlib.contextmanager
def created_instances(query_set):
    u"""
    Returns model instances created inside a context block.

    Example:
        User.objects.create('john')
        with created_instances(User.objects) as query_set:
            User.objects.create('george')
        new_user = query_set.get()
    """
    original_pk = (o.pk for o in query_set.all())
    yield query_set.exclude(pk__in=original_pk)

@contextlib.contextmanager
def patch_with_exception(target):
    u"""
    Patches ``target`` with dummy function that always raises an exception. The raised
    exception is catched after it bubbles out of the context. Usefull if you want to test how
    the code reacts to unexpected exceptions.
    """
    class MockException(Exception):
        pass
    def mock_func(*args, **kwargs):
        raise MockException
    with mock.patch(target, mock_func):
        try:
            yield
        except MockException:
            pass

@contextlib.contextmanager
def reload_for_context(manager, module):
    u"""
    Reloads ``module`` after entering and after exiting context created by given context ``manager``. Usefull if you
    want to override Django settings that are read only during the module initialization. By reloading the module, the
    overriden settings are read again.

    Note that this cannot be implemented by nested contexts as we need to reload the module both after the original
    context is entered and as well as after the original context is exited. Nested contexts would reload the module
    either before the original context was entered or before it was exited, depending on the contexts order.

    Example:
        with reload_for_context(self.settings(CRON_TIMES=['10:00', '14:00']), 'app.cron') as context:
            call_command(u'runcrons')
    """
    module = importlib.import_module(module)
    try:
        with manager as context:
            importlib.reload(module)
            yield context
    finally:
        importlib.reload(module)

class ViewTestCaseMixin(TestCase):

    def assert_allowed_http_methods(self, allowed, url):
        u"""
        Makes requests with all http methods to the given ``url`` and checks that only ``allowed``
        methods are allowed. Method that are not allowed should give "405: Method not Allowed"
        status code. Usefull for testing views decorated with ``@require_http_methods()``
        decorator.

        Example:
            @require_http_methods([u'HEAD', u'GET'])
            def some_view(request):
                return HttpResponse()

            class SomeViewTestCase(ViewTestCaseMixin, TestCase):
                def test_methods(self):
                    allowed = [u'HEAD', u'GET']
                    self.assert_allowed_http_methods(allowed, reverse('some_view'))
        """
        methods = [u'HEAD', u'GET', u'POST', u'OPTIONS', u'PUT', u'PATCH', u'DELETE']
        allow_headers = []
        for method in methods:
            response = getattr(self.client, method.lower())(url)
            if method in allowed:
                self.assertNotEqual(response.status_code, 405, u'{} is not allowed'.format(method))
            else:
                self.assertEqual(response.status_code, 405, u'{} is allowed'.format(method))
                allow_headers.append(response[u'Allow'])
        for header in allow_headers:
            self.assertItemsEqual(header.split(u', '), allowed)

    def assert_anonymous_user_is_redirected(self, url, method=u'GET'):
        u"""
        Makes anonymous request to the given ``url`` and checks that the request gets redirected to
        the login page. Usefull for testing views decorated with ``@login_required`` decorator.

        Example:
            @login_required
            def some_view(request):
                return HttpResponse()

            class SomeViewTestCase(ViewTestCaseMixin, TestCase):
                def test_anonymous(self):
                    self.assert_anonymous_user_is_redirected(reverse('some_view'))
                def test_anonymous_post(self):
                    self.assert_anonymous_user_is_redirected(reverse('some_view'), method='POST')
        """
        response = getattr(self.client, method.lower())(url, follow=True)
        expected_url = reverse(u'account_login') + u'?' + urlencode({u'next': url})
        self.assertRedirects(response, expected_url)
