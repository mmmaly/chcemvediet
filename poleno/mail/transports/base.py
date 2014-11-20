# vim: expandtab
# -*- coding: utf-8 -*-

class BaseTransport(object):
    def __init__(self):
        pass

    def __enter__(self):
        self.connect()
        return self

    def __exit__(self, type, value, traceback):
        self.disconnect()

    def connect(self):
        pass

    def disconnect(self):
        pass

    def send_message(self, message):
        raise NotImplementedError

    def get_messages(self):
        raise NotImplementedError
