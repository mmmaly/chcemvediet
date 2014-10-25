# vim: expandtab
# -*- coding: utf-8 -*-
import contextlib

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
