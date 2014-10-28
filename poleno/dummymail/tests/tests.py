# vim: expandtab
# -*- coding: utf-8 -*-
import mock
import localmail

from django.core.management import call_command
from django.test import TestCase

from poleno.utils.misc import collect_stdout

class DummymailCommand(TestCase):
    u"""
    Tests ``dummymail`` management command. Only checks if ``localmail`` processes are spawned with
    ``multiprocessing`` module. Does not chech if ``localmail`` works.
    """

    def _call_dummymail(self, *args, **kwargs):
        mock_process = mock.Mock()
        mock_time = mock.Mock()
        mock_time.sleep.side_effect = KeyboardInterrupt
        with mock.patch.multiple(u'poleno.dummymail.management.commands.dummymail', Process=mock_process, time=mock_time):
            with collect_stdout():
                call_command(u'dummymail', *args, **kwargs)
        return mock_process

    def test_with_default_ports(self):
        mock_process = self._call_dummymail()
        self.assertItemsEqual(mock_process.mock_calls, [
            mock.call(target=localmail.run, args=(1025, 1143)),
            mock.call().start(),
            mock.call(target=localmail.run, args=(2025, 2143)),
            mock.call().start(),
            ])

    def test_with_explicit_ports(self):
        mock_process = self._call_dummymail(
                outgoing_smtp_port=1001, outgoing_imap_port=1002,
                incoming_smtp_port=1003, incoming_imap_port=1004)
        self.assertItemsEqual(mock_process.mock_calls, [
            mock.call(target=localmail.run, args=(1001, 1002)),
            mock.call().start(),
            mock.call(target=localmail.run, args=(1003, 1004)),
            mock.call().start(),
            ])
