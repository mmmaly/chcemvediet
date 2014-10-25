# vim: expandtab
# -*- coding: utf-8 -*-
import mock

from django.dispatch.dispatcher import Signal
from django.test import TestCase

from ..test import override_signals

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
