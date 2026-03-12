# vim: expandtab
# -*- coding: utf-8 -*-
import os
import sys
import random
import string
import re
import mimetypes
import contextlib
import collections
from functools import wraps
from StringIO import StringIO
from unidecode import unidecode



class Bunch(object):
    u"""
    Simple object with defened attributes.

    Source:
    http://code.activestate.com/recipes/52308-the-simple-but-handy-collector-of-a-bunch-of-named/

    Example:
        b = Bunch(key=value)
        b.key
        b.other = value
        del b.key
    """

    def __init__(self, **kwargs):
        vars(self).update(kwargs)

class FormatMixin(object):

    def __format__(self, format):
        try:
            u = unicode(self)
        except UnicodeError:
            u = u'[Bad Unicode data]'
        return u'<{}: {}>'.format(self.__class__.__name__, u)

    def __repr__(self):
        return format(self).encode(u'utf-8')

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
    consonants `[bcdfghjklmnprstvxz]`. You can use ``vowels`` and ``consonants`` arguments to set
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

def ensure_tuple(value):
    if isinstance(value, tuple):
        return value
    elif isinstance(value, list):
        return tuple(value)
    else:
        return (value,)

def slugify(s):
    u"""
    This slugify transliretares all supported non-latin characters to latin. For instance it
    transliterates german "ẞ" to "ss". It's better than django.utils.text.slugify which throws away
    all non-latin characters.
    """
    return u'-'.join(w for w in re.split(r'[^a-z0-9]+', unidecode(s).lower()) if w)

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

def guess_extension(content_type, default=u'.bin'):
    u"""
    Guesses file extension based on file content type. Wrapper around ``mimetypes.guess_extension``
    to return ``default`` extension if the given content type is not known by ``mimetypes`` module,
    and to fix stupid guesses like: "text/plain" -> ".ksh".

    See: http://bugs.python.org/issue1043134

    Example:
        "text/plain" -> ".txt"
        "text/html" -> ".html"
    """
    override = {
            u'text/plain': u'.txt', # was: ".ksh"
            u'text/html': u'.html', # was: ".htm"
            u'application/octet-stream': u'.bin', # was: ".obj"
            }
    if content_type in override:
        res = override[content_type]
    else:
        res = mimetypes.guess_extension(content_type)
    if not res:
        res = default
    return res

def sanitize_filename(filename, content_type, default_base=u'attachment'):
    u"""
    Sanitize file name and adjust its extension according to given ``content_type``. Remove all
    control characters (with ASCII code below 32) from the file name and shorten it to a maximum of
    200 characters. If the resulting file name excluding the extension is empty, use
    ``default_base`` instead of it. Adjust file extension if the given ``content_type`` differs from
    the content type represented by the original file extension to a correct one.

    Example:
        "qwer\x01\x02ty.txt", "text/plain" -> "qwerty.txt"
        "qwerty.txt", "application/octet-stream" -> "qwerty.bin"
        "\x01.txt", "text/plain" -> "attachment.txt"
    """
    return adjust_extension(sanitize_basename(filename, default_base), content_type)

def sanitize_basename(filename, default_base=u'attachment'):
    u"""
    Remove all control characters (with ASCII code below 32) from the base and shorten it to
    a maximum of 200 characters. If the resulting base excluding the extension is empty, use
    ``default_base`` instead of it.

    Example:
        "qwer\x01\x02ty.abc" -> "qwerty.abc"
        "\x01.txt", "text/plain" -> "attachment.txt"
    """
    base, extension = os.path.splitext(filename)
    base = ''.join([c for c in base if ord(c) >= 32][:200]) or default_base
    return base + extension

def adjust_extension(filename, content_type):
    u"""
    Adjust file extension if the given ``content_type`` differs from the content type represented by
    the original file extension to a correct one.

    Example:
        "qwerty.txt", "application/pdf" -> "qwerty.pdf"
        "qwerty.txt", "text/plain" -> "qwerty.txt"
        "qwerty.bin", None -> "qwerty.bin"
    """
    if content_type and mimetypes.guess_type(filename)[0] != content_type:
        return os.path.splitext(filename)[0] + guess_extension(content_type)
    return filename

def filesize(size):
    u"""
    Formats file sizes in bytes into a human readable form.

    Example:
        0 -> "0 bytes"
        1023 -> "1023 bytes"
        49573834547 -> "46.2 GB"
        -3847 -> "-3.7 kB"
    """
    if size is None:
        return None

    for fmt in [u'{:.0f} bytes', u'{:.1f} kB', u'{:.1f} MB', u'{:.1f} GB', u'{:.1f} TB']:
        if abs(size) < 1024.0:
            return fmt.format(round(size + 0.04999, 1))
        size /= 1024.0
    return u'{:.1f} PB'.format(round(size + 0.04999, 1))

def parsefilesize(value):
    u"""
    Parses files sizes formatted with `filesize` function above.

    Example:
        "0 bytes" -> 0.0
        "1023 bytes" -> 1023.0
        "46.2 GB" -> 49606872268.8
        "-3.8 kB" -> -3891.2
    """
    base = 1
    for unit in [u'bytes', u'kB', u'MB', u'GB', u'TB', u'PB']:
        if value.endswith(unit):
            return float(value[:-len(unit)]) * base
        base *= 1024.0
    raise ValueError

@contextlib.contextmanager
def collect_stdout():
    u"""
    Intercepts and collencts all output printed on ``stdout``.

    Example:
        with collect_stdout() as collect:
            print('Hello')
        return 'printed: "{}"'.format(collect.stdout)
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
                print('Moo.foo({})'.format(value))
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
        @wraps(method)
        def wrapped_method(self, *args):
            cache = self.__dict__.setdefault(u'_{}__cache'.format(method.__name__), {})
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

def print_invocations(func=None):
    if not hasattr(print_invocations, u'level'):
        print_invocations.level = 0
    @wraps(func)
    def wrapped_func(*args, **kwargs):
        print(u'{}>{}: args={} kwargs={}'.format(
                u'  '*print_invocations.level, func.__name__,
                unicode(repr(args), u'utf-8'), unicode(repr(kwargs), u'utf-8')))
        print_invocations.level += 1
        res = func(*args, **kwargs)
        print_invocations.level -= 1
        print(u'{}<{}: res={}'.format(u'  '*print_invocations.level, func.__name__,
                unicode(repr(res), u'utf-8')))
        return res
    return wrapped_func
