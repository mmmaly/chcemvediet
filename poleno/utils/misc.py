# vim: expandtab
# -*- coding: utf-8 -*-
import sys
import random
import string
import mimetypes
import contextlib
import collections
from functools import wraps
from StringIO import StringIO

from django.utils.decorators import available_attrs

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

def try_except(func, failure=None, *exceptions):
    u"""
    Inline try-except block.

    Example:
        a = dict(moo=3, foo=4)
        b = try_except(lambda: a.goo, 7, KeyError)
    """
    if not exceptions:
        exceptions = (Exception,)
    try:
        return func()
    except exceptions:
        return failure() if callable(failure) else failure

def nop():
    pass

def squeeze(s):
    u"""
    Substitutes all whitespace including new lines with single spaces, striping any leading or
    trailing whitespace.

    Example:
        "   text   with\nspaces\n\n" -> "text with spaces"
    """
    return u' '.join(s.split())

def norm_new_lines(s):
    u"""
    Normalize new lines.
    """
    if s is None:
        return None
    return s.replace('\r\n','\n').replace('\r','\n')

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

def filesize(size):
    u"""
    Formats file sizes in bytes into a human readable form.

    Example:
        0 -> "0 bytes"
        1023 -> "1023 bytes"
        49573834547 -> "46.2 GB"
        -3847 -> "-3.8 kB"
    """
    for fmt in ['%.0f bytes', u'%.1f kB', u'%.1f MB', u'%.1f GB', u'%.1f TB']:
        if abs(size) < 1024.0:
            return fmt % size
        size /= 1024.0
    return u'%.1f PB' % size

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

def cached_method(method=None, cached_exceptions=None):
    u"""
    Decorator to cache class methods. Cache is kept per instance in ``self._{methodname}__cache``
    attribute. Pass a list of exception types to ``cached_exceptions`` to intercept and cache
    matching exceptions as well. Exceptions that do not match are not touched.

    Example:
        class Moo(object):
            @cached_method(cached_exceptions=ValidationError)
            def foo(self, value):
                print('Moo.foo(%s)' % value)
                if value == 1:
                    return 4
                if value == 2:
                    raise ValueError
                raise ValidationError('Boo')

        Returned value is cached:
        >>> a = Moo()
        >>> a.foo(1)
        Moo.foo(1)
        4
        >>> a.foo(1)
        4

        ValueError exception is not cached:
        >>> a = Moo()
        >>> a.foo(2)
        Moo.foo(2)
        ValueError
        >>> a.foo(2)
        Moo.foo(2)
        ValueError

        ValidationError exception is cached:
        >>> a = Moo()
        >>> a.foo(3)
        Moo.foo(3)
        ValidationError
        >>> a.foo(3)
        ValidationError
    """
    def actual_decorator(method):
        @wraps(method, assigned=available_attrs(method))
        def wrapped_method(self, *args):
            cache = self.__dict__.setdefault(u'_%s__cache' % method.__name__, {})
            try:
                res, exc = cache[args]
            except KeyError:
                try:
                    res = method(self, *args)
                except cached_exceptions as exc:
                    res = None
                else:
                    exc = None
                cache[args] = res, exc
            if exc is None:
                return res
            else:
                raise exc
        return wrapped_method
    if method:
        return actual_decorator(method)
    return actual_decorator
