# vim: expandtab
# -*- coding: utf-8 -*-
import mock

from django.views.decorators.http import require_http_methods
from django.http import HttpResponse
from django.dispatch.dispatcher import Signal
from django.conf.urls import patterns, url
from django.contrib.auth.models import User
from django.test import TestCase

from poleno.utils.views import login_required

from ..test import override_signals, created_instances, ViewTestCaseMixin

class OverrideSignalsTest(TestCase):
    u"""
    Tests ``override_signals()`` context manager.
    """

    def test_original_receiver_does_not_get_overriden_signal(self):
        u"""
        Checks that receivers registered outside ``override_signals`` context do not get signals
        emitted inside the context block.
        """
        signal = Signal(providing_args=[u'message'])
        original_receiver = mock.Mock()
        signal.connect(original_receiver)
        signal.send(sender=None, message=u'before')
        with override_signals(signal):
            signal.send(sender=None, message=u'overriden')
        signal.send(sender=None, message=u'after')
        self.assertEqual(original_receiver.mock_calls, [
            mock.call(message=u'before', sender=None, signal=signal),
            mock.call(message=u'after', sender=None, signal=signal),
            ])

    def test_new_receiver_gets_only_overriden_signal(self):
        u"""
        Checks that receivers registered inside ``override_signals`` context get only signals
        emitted inside the context block.
        """
        signal = Signal(providing_args=[u'message'])
        signal.send(sender=None, message=u'before')
        with override_signals(signal):
            new_receiver = mock.Mock()
            signal.connect(new_receiver)
            signal.send(sender=None, message=u'overriden')
        signal.send(sender=None, message=u'after')
        self.assertEqual(new_receiver.mock_calls, [
            mock.call(message=u'overriden', sender=None, signal=signal),
            ])

    def test_with_multiple_signals(self):
        signal1 = Signal(providing_args=[u'message'])
        signal2 = Signal(providing_args=[u'message'])
        original_receiver = mock.Mock()
        signal1.connect(original_receiver)
        signal2.connect(original_receiver)
        signal1.send(sender=None, message=u'before')
        signal2.send(sender=None, message=u'before')
        with override_signals(signal1, signal2):
            new_receiver = mock.Mock()
            signal1.connect(new_receiver)
            signal2.connect(new_receiver)
            signal1.send(sender=None, message=u'overriden')
            signal2.send(sender=None, message=u'overriden')
        signal1.send(sender=None, message=u'after')
        signal2.send(sender=None, message=u'after')
        self.assertEqual(original_receiver.mock_calls, [
            mock.call(message=u'before', sender=None, signal=signal1),
            mock.call(message=u'before', sender=None, signal=signal2),
            mock.call(message=u'after', sender=None, signal=signal1),
            mock.call(message=u'after', sender=None, signal=signal2),
            ])
        self.assertEqual(new_receiver.mock_calls, [
            mock.call(message=u'overriden', sender=None, signal=signal1),
            mock.call(message=u'overriden', sender=None, signal=signal2),
            ])

class CreatedInstancesTest(TestCase):
    u"""
    Tests ``created_instances()`` context manager.
    """

    def test_created_instances(self):
        user1 = User.objects.create_user(u'john')
        with created_instances(User.objects) as query_set:
            user2 = User.objects.create_user(u'george')
            user3 = User.objects.create_user(u'sam')
        self.assertItemsEqual(query_set.all(), [user2, user3])

    def test_created_instances_with_no_created_instances(self):
        user1 = User.objects.create_user(u'john')
        with created_instances(User.objects) as query_set:
            pass
        self.assertItemsEqual(query_set.all(), [])

    def test_created_instances_with_no_original_instances(self):
        self.assertEqual(User.objects.count(), 0)
        with created_instances(User.objects) as query_set:
            user = User.objects.create_user(u'john')
        self.assertItemsEqual(query_set.all(), [user])

class ViewTestCaseMixinAssertAllowedHttpMethodsTest(ViewTestCaseMixin, TestCase):
    u"""
    Tests ``assert_allowed_http_methods()`` method of ``ViewTestCaseMixin`` class.
    """

    @require_http_methods([u'HEAD', u'GET'])
    def mock_view(request):
        return HttpResponse()

    urls = tuple(patterns(u'',
        url(r'^$', mock_view),
    ))

    def test_with_all_methods_allowed_as_expected(self):
        allowed = [u'HEAD', u'GET']
        self.assert_allowed_http_methods(allowed, u'/')

    def test_with_allowed_method_which_should_not_be_allowed(self):
        allowed = [u'HEAD']
        with self.assertRaisesMessage(AssertionError, u'GET is allowed'):
            self.assert_allowed_http_methods(allowed, u'/')

    def test_with_not_allowed_method_which_shoud_be_allowed(self):
        allowed = [u'HEAD', u'GET', u'POST']
        with self.assertRaisesMessage(AssertionError, u'POST is not allowed'):
            self.assert_allowed_http_methods(allowed, u'/')

    def test_invalid_method(self):
        allowed = [u'HEAD', u'GET', u'INVALID']
        with self.assertRaisesMessage(AssertionError, u'Element counts were not equal'):
            self.assert_allowed_http_methods(allowed, u'/')

class ViewTestCaseMixinAssertAnonymousUserIsRedirected(ViewTestCaseMixin, TestCase):
    u"""
    Tests ``assert_anonymous_user_is_redirected()`` method of ``ViewTestCaseMixin`` class.
    """

    @login_required
    def with_login_required_view(request):
        pass

    def without_login_required_view(request):
        return HttpResponse()

    def login_view(request):
        return HttpResponse()

    urls = tuple(patterns(u'',
        url(r'^with_login_required/$', with_login_required_view, name=u'aa'),
        url(r'^without_login_required/$', without_login_required_view),
        url(r'^accounts/login/$', login_view, name=u'account_login'),
    ))

    def test_on_wiew_with_login_required_passes(self):
        with mock.patch(u'poleno.utils.test.urlencode', return_value=u'next=/with_login_required/'):
            self.assert_anonymous_user_is_redirected(u'/with_login_required/')

    def test_on_wiew_without_login_required_fails(self):
        with self.assertRaisesMessage(AssertionError, u"Response didn't redirect as expected: Response code was 200"):
            self.assert_anonymous_user_is_redirected(u'/without_login_required/')

    def test_with_custom_method_on_wiew_with_login_required_passes(self):
        with mock.patch(u'poleno.utils.test.urlencode', return_value=u'next=/with_login_required/'):
            self.assert_anonymous_user_is_redirected(u'/with_login_required/', method=u'POST')

    def test_with_custom_method_on_wiew_without_login_required_fails(self):
        with self.assertRaisesMessage(AssertionError, u"Response didn't redirect as expected: Response code was 200"):
            self.assert_anonymous_user_is_redirected(u'/without_login_required/', method=u'POST')
