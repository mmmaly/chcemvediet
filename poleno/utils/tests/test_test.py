# vim: expandtab
# -*- coding: utf-8 -*-
import mock

from django.http import HttpResponse
from django.dispatch.dispatcher import Signal
from django.conf.urls import patterns, url
from django.contrib.auth.models import User
from django.test import TestCase

from ..test import override_signals, created_instances, SecureClient

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

class SecureClientTest(TestCase):
    u"""
    Tests ``SecureClient`` test client class.
    """
    def mock_view(request):
        return HttpResponse(u'is_secure=%s, port=%s, scheme=%s'
                % (request.is_secure(), request.META[u'SERVER_PORT'], request.META[u'wsgi.url_scheme']))

    client_class = SecureClient
    urls = tuple(patterns(u'',
        url(r'^$', mock_view),
    ))

    def test_secure_request(self):
        response = self.client.get(u'/', secure=True)
        self.assertEqual(response.content, u'is_secure=True, port=443, scheme=https')

    def test_non_secure_request(self):
        response = self.client.get(u'/', secure=False)
        self.assertEqual(response.content, u'is_secure=False, port=80, scheme=http')

    def test_request_is_non_secure_by_default(self):
        response = self.client.get(u'/')
        self.assertEqual(response.content, u'is_secure=False, port=80, scheme=http')
