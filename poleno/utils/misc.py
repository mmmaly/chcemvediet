# vim: expandtab
# -*- coding: utf-8 -*-
import sys
import random
import string
import mimetypes
import contextlib
import collections
from StringIO import StringIO

class Bunch(object):
    u"""
    Simple object with defened attributes.

    Source: http://code.activestate.com/recipes/52308-the-simple-but-handy-collector-of-a-bunch-of-named/

    Example:
        b = Bunch(key=value)
        b.key
        b.other = value
        del b.key
    """

    def __init__(self, **kwargs):
        vars(self).update(kwargs)

def random_string(length, chars=(string.ascii_letters + string.digits)):
    u"""
    Returns a random string ``length`` characters long consisting of ``chars``.
    """
    sysrandom = random.SystemRandom()
    return u''.join(sysrandom.choice(chars) for i in xrange(length))

def random_readable_string(length, vowels=u'aeiouy', consonants=u'bcdfghjklmnprstvxz'):
    u"""
    Returns a random string ``length`` characters long of the following form. Every string is
    generated with equal probability.

    [:vowel:]? ([:consonant:][:vowel:])* [:consonant:]?

    Where `[:vowel:]` is the set of all vowels `[aeiouy]` and `['consonant']` is the set of
    consonants `[bcdfghjklmnprstvxz]`. Use can use ``vowels`` and ``consonants`` arguments to set
    your own sets of vowels and consonants.
    """
    res = []
    sysrandom = random.SystemRandom()
    if sysrandom.random() < len(vowels) / float(len(vowels) + len(consonants)):
        res.append(sysrandom.choice(vowels))
    while len(res) < length:
        res.append(sysrandom.choice(consonants))
        if len(res) < length:
            res.append(sysrandom.choice(vowels))
    return u''.join(res)

def squeeze(s):
    u"""
    Substitutes all whitespace including new lines with single spaces, striping any leading or
    trailing whitespace.

    Example:
        "   text   with\nspaces\n\n" -> "text with spaces"
    """
    return u' '.join(s.split())

def flatten(l):
    u"""
    Recursively flattens list of lists of lists.

    Example:
       [] -> []
       [1, 2, (3, 4, (), (5,), [[[[6]]]],)] -> [1, 2, 3, 4, 5, 6]
       ['one', ['two', 'three']] -> ['one', 'two', 'three']
    """
    for el in l:
        if isinstance(el, collections.Iterable) and not isinstance(el, basestring):
            for sub in flatten(el):
                yield sub
        else:
            yield el

def guess_extension(content_type, default=None):
    u"""
    Guesses file extention based on file content type. Wrapper around ``mimetypes.guess_extension`` to
    return ``default`` extension if the given content type is not known by ``mimetypes`` module, and to
    fix stupid guesses like: "text/plain" -> ".ksh".

    See: http://bugs.python.org/issue1043134

    Example:
        "text/plain" -> ".txt"
        "text/html" -> ".html"
    """
    override = {
            u'text/plain': u'.txt', # was: ".ksh"
            u'application/octet-stream': u'.bin', # was: ".obj"
            }
    if content_type in override:
        res = override[content_type]
    else:
        res = mimetypes.guess_extension(content_type)
    if not res:
        res = default
    return res

@contextlib.contextmanager
def collect_stdout():
    u"""
    Intercepts and collencts all output printed on ``stdout``.

    Example:
        with collect_stdout() as collect:
            print('Hello')
        return 'printed: "%s"' % collect.stdout
    """
    orig_stdout = sys.stdout
    new_stdout = sys.stdout = StringIO()
    res = Bunch(stdout=None)
    try:
        yield res
    finally:
        new_stdout.seek(0)
        res.stdout = new_stdout.read()
        sys.stdout = orig_stdout

def decorate(func=None, **kwargs):
    u"""
    Decorates given function with attributes. May be used as a decorator or a function.

    Example:
        @decorate(moo=4, foo=7)
        @decorate(goo=47)
        def func():
            pass

        Now we have:
            func.moo == 4
            func.foo == 7
            func.goo == 47

    Example:
        func = decorate(lambda a: a+a, moo=4, foo=7)

        Again we have:
            func.moo == 4
            func.foo == 7
    """
    def actual_decorator(func):
        for key, val in kwargs.iteritems():
            setattr(func, key, val)
        return func
    if func:
        return actual_decorator(func)
    else:
        return actual_decorator
