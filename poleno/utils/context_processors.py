# vim: expandtab
# -*- coding: utf-8 -*-
import itertools


class IdGenerator(object):
    u"""
    Generates unique integer ids for HTML elements rendered within one request. Templates use
    ``{{ idgenerator.next }}``. On Python 2 that called ``itertools.count().next()``; Python 3
    generators only have ``__next__``, so the template got an empty string and every collapsible
    panel ended up with ``id=""`` and ``data-target="#"``.
    """

    def __init__(self, start=1):
        self._counter = itertools.count(start)

    def next(self):
        return next(self._counter)

    def __next__(self):
        return self.next()

    def __iter__(self):
        return self


def idgenerator(request):
    return {
            u'idgenerator': IdGenerator(1),
            }
