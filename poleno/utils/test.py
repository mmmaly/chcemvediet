# vim: expandtab
# -*- coding: utf-8 -*-
import contextlib

from django.test import Client

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
