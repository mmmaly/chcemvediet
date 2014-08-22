# vim: expandtab
# -*- coding: utf-8 -*-

class Bunch(object):
    """
    Simple object with defened attributes.

    Source: http://code.activestate.com/recipes/52308-the-simple-but-handy-collector-of-a-bunch-of-named/

    Example:
        b = Bunch(key=value)
        b.key
        b.other = value
    """

    def __init__(self, **kwargs):
        self.__dict__.update(kwargs)

