# vim: expandtab
# -*- coding: utf-8 -*-
import re
import string
import random

from django.test import TestCase

from poleno.utils.misc import (Bunch, random_string, random_readable_string, try_except, squeeze,
        flatten, guess_extension, filesize, collect_stdout, decorate, cached_method)

class BunchTest(TestCase):
    u"""
    Tests ``Bunch`` class. Checks that the bunch contains all defined attributes, does not contain
    undefined attributes, and that we may add, change and remove attributes from the bunch.
    """

    def test_defined_attribute(self):
        bunch = Bunch(first=1, second=u'second')
        self.assertEqual(bunch.first, 1)
        self.assertEqual(bunch.second, u'second')

    def test_undefined_attribute(self):
        bunch = Bunch(first=1, second=u'second')
        with self.assertRaises(AttributeError):
            bunch.nop

    def test_add_attribute(self):
        bunch = Bunch(first=1, second=u'second')
        with self.assertRaises(AttributeError):
            bunch.third
        bunch.third = [1, 2, 3]
        self.assertEqual(bunch.third, [1, 2, 3])

    def test_change_attribute(self):
        bunch = Bunch(first=1, second=u'second')
        self.assertEqual(bunch.first, 1)
        bunch.first = u'changed'
        self.assertEqual(bunch.first, u'changed')

    def test_delete_attribute(self):
        bunch = Bunch(first=1, second=u'second')
        self.assertEqual(bunch.first, 1)
        del bunch.first
        with self.assertRaises(AttributeError):
            bunch.first

    def test_empty_bunch(self):
        bunch = Bunch()
        with self.assertRaises(AttributeError):
            bunch.first

class RandomStringTest(TestCase):
    u"""
    Tests ``random_string()`` function. Checks that the random string has correct length and
    consists of allowed characters only.
    """

    def _check(self, length, chars):
        pattern = r'^[{chars}]*$'.format(chars=re.escape(chars))

        res = random_string(length, chars)
        self.assertEqual(len(res), length)
        self.assertRegexpMatches(res, pattern)

    def test_ascii_letters(self):
        for length in range(20):
            self._check(length, string.ascii_letters)

    def test_long_string_with_punctuation(self):
        self._check(1234, string.ascii_letters + string.digits + string.punctuation)
        self._check(1235, string.ascii_letters + string.digits + string.punctuation)

class RandomReadableStringTest(TestCase):
    u"""
    Tests ``random_readable_string()`` function. Checks that the random string has correct length,
    consists of allowed characters only and has correct structure.
    """

    def _check(self, length, vowels, consonants):
        pattern = r'^[{vowels}]?([{consonants}][{vowels}])*[{consonants}]?$'.format(
                vowels=re.escape(vowels), consonants=re.escape(consonants))

        res = random_readable_string(length, vowels, consonants)
        self.assertEqual(len(res), length)
        self.assertRegexpMatches(res, pattern)


    def test_with_vowels_and_consonants(self):
        for length in range(1, 20):
            self._check(length, u'aeiouy', u'bcdfghjklmnprstvxz')

    def test_with_letters_and_punctuation(self):
        for length in range(1, 20):
            self._check(length, string.ascii_letters, string.punctuation)

    def test_with_default_argumnts(self):
        for length in range(1, 20):
            res = random_readable_string(length)
            self.assertEqual(len(res), length)

class TryExceptTest(TestCase):
    u"""
    Tests ``try_except()`` function.
    """

    def test_catched_exception(self):
        a = dict(moo=4)
        b = try_except(lambda: a[u'foo'], 7, KeyError)
        self.assertEqual(b, 7)

    def test_uncatched_exception(self):
        a = dict(moo=4)
        with self.assertRaises(KeyError):
            try_except(lambda: a[u'foo'], 7, ValueError)

    def test_without_exception(self):
        a = dict(moo=4)
        b = try_except(lambda: a[u'moo'], 7, KeyError)
        self.assertEqual(b, 4)

    def test_with_multiple_exception_classes(self):
        a = dict(moo=4)
        b = try_except(lambda: a[u'foo'], 7, ValueError, KeyError, IndexError)
        self.assertEqual(b, 7)

    def test_with_no_exception_classes(self):
        a = dict(moo=4)
        b = try_except(lambda: a[u'foo'], 7)
        self.assertEqual(b, 7)

    def test_with_callable_failture(self):
        a = dict(moo=4)
        b = try_except(lambda: a[u'foo'], lambda: a[u'moo'])
        self.assertEqual(b, 4)

class SqueezeTest(TestCase):
    u"""
    Tests ``squeeze()`` function.
    """

    def test_trim(self):
        self.assertEqual(squeeze(u'  left'), u'left')
        self.assertEqual(squeeze(u'right      '), u'right')
        self.assertEqual(squeeze(u' both '), u'both')
        self.assertEqual(squeeze(u'\n\n\n111\n\n\n'), u'111')
        self.assertEqual(squeeze(u'    aaa fff    rrr   '), u'aaa fff rrr')

    def test_linebreaks_and_tabs(self):
        self.assertEqual(squeeze(u'\n\n1\t2\r\r3\r\n4\n\r5\r\r6\n\n7'), u'1 2 3 4 5 6 7')
        self.assertEqual(squeeze(u'1 \n2\n\n 3     \t   4\n\n\n\n\n\n\n\n\n5'), u'1 2 3 4 5')

    def test_only_whitespace(self):
        self.assertEqual(squeeze(u' '), u'')
        self.assertEqual(squeeze(u'               '), u'')
        self.assertEqual(squeeze(u'  \n\n  \n\t\t\r\r\r\n\n'), u'')
        self.assertEqual(squeeze(u'\n\n\n\n\n\n\n\n\n\n'), u'')
        self.assertEqual(squeeze(u'\t\t\t\t'), u'')
        self.assertEqual(squeeze(u'\r'), u'')

    def test_empty_string(self):
        self.assertEqual(squeeze(u''), u'')

    def test_long_text(self):
        res = squeeze(u"""
                Lorem ipsum dolor sit amet, consectetur adipiscing elit, sed do eiusmod tempor
                incididunt ut labore et dolore magna aliqua. Ut enim ad minim veniam, quis nostrud
                exercitation ullamco laboris nisi ut aliquip ex ea commodo consequat. Duis aute
                irure dolor in reprehenderit in voluptate velit esse cillum dolore eu fugiat nulla
                pariatur. Excepteur sint occaecat cupidatat non proident, sunt in culpa qui officia
                deserunt mollit anim id est laborum.
                """)
        self.assertRegexpMatches(res, r'^(\S+ )*\S+$')

    def test_long_random_text(self):
        sample = u''.join(random.choice(string.printable if random.random() < 0.5 else string.whitespace)
                for i in range(1000))
        res = squeeze(sample)
        self.assertRegexpMatches(res, r'^(\S+ )*\S+$')

class FlattenTest(TestCase):
    u"""
    Tests ``flatten()`` function.
    """

    def test_list_with_tuples(self):
        result = flatten([1, 2, (3, 4, (), (5,), [[[[6]]]],)])
        self.assertEqual(list(result), [1, 2, 3, 4, 5, 6])

    def test_list_with_strings(self):
        result = flatten([u'one', [u'two', u'three']])
        self.assertEqual(list(result), ['one', 'two', 'three'])

    def test_empty_list(self):
        result = flatten([])
        self.assertEqual(list(result), [])

    def test_list_with_multiple_references_to_the_same_list(self):
        a = [1, 2, 3]
        b = [a, a, a]
        result = flatten(b)
        self.assertEqual(list(result), [1, 2, 3, 1, 2, 3, 1, 2, 3])

    def test_list_with_circular_references_raises_error(self):
        a = [1, 2, 3]
        a[0] = a
        with self.assertRaisesMessage(RuntimeError, u'maximum recursion depth exceeded'):
            list(flatten(a))

class GuessExtensionTest(TestCase):
    u"""
    Tests ``guess_extension()`` function.
    """

    # Overriden guesses
    def test_text_plain(self):
        self.assertEqual(guess_extension(u'text/plain'), u'.txt')

    def test_application_octet_stream(self):
        self.assertEqual(guess_extension(u'application/octet-stream'), u'.bin')

    # Guesses by ``mimetypes`` module
    def test_application_pdf(self):
        self.assertEqual(guess_extension(u'application/pdf'), u'.pdf')

    def test_unknown_content_type(self):
        self.assertIsNone(guess_extension(u'application/nonexistent'))

    def test_unknown_content_type_with_default_extension(self):
        self.assertEqual(guess_extension(u'application/nonexistent', u'.bin'), u'.bin')

class FileSize(TestCase):
    u"""
    Tests ``filesize()`` function.
    """

    def test_zero_bytes(self):
        self.assertEqual(filesize(0), u'0 bytes')

    def test_supported_sizes(self):
        self.assertEqual(filesize(1023), u'1023 bytes')
        self.assertEqual(filesize(1024), u'1.0 kB')
        self.assertEqual(filesize(1024*1024), u'1.0 MB')
        self.assertEqual(filesize(1024*1024*1024), u'1.0 GB')
        self.assertEqual(filesize(1024*1024*1024*1024), u'1.0 TB')
        self.assertEqual(filesize(1024*1024*1024*1024*1024), u'1.0 PB')

    def test_too_big_sizes(self):
        self.assertEqual(filesize(1024*1024*1024*1024*1024*1024), u'1024.0 PB')
        self.assertEqual(filesize(1024*1024*1024*1024*1024*1024*1024), u'1048576.0 PB')

    def test_random_sizes(self):
        self.assertEqual(filesize(3847), u'3.8 kB')
        self.assertEqual(filesize(3834547), u'3.7 MB')
        self.assertEqual(filesize(49573834547), u'46.2 GB')
        self.assertEqual(filesize(344749573834547), u'313.5 TB')

    def test_negative_sizes(self):
        self.assertEqual(filesize(-47), u'-47 bytes')
        self.assertEqual(filesize(-3847), u'-3.8 kB')

class CollectStdoutTest(TestCase):
    u"""
    Tests ``collect_stdout()`` context manager.
    """

    def test_stdout_collected(self):
        with collect_stdout() as collected:
            print(u'Collected text')
        self.assertEqual(collected.stdout, u'Collected text\n')

    def test_stdout_released_after_block(self):
        with collect_stdout() as outer:
            print(u'Outer before')
            with collect_stdout() as inner:
                print(u'Inner')
            print(u'Outer after')
        self.assertEqual(inner.stdout, u'Inner\n')
        self.assertEqual(outer.stdout, u'Outer before\nOuter after\n')

class DecorateTest(TestCase):
    u"""
    Tests ``decorate()`` decorator.
    """

    def test_as_decorator(self):
        @decorate(moo=4, foo=7)
        @decorate(goo=47)
        def func(a, b):
            return a + b

        self.assertEqual(func.moo, 4)
        self.assertEqual(func.foo, 7)
        self.assertEqual(func.goo, 47)
        self.assertEqual(func(2, 3), 5)

    def test_as_function(self):
        func = decorate(lambda a, b: a + b, moo=4, foo=7)

        self.assertEqual(func.moo, 4)
        self.assertEqual(func.foo, 7)
        self.assertEqual(func(2, 3), 5)

class CachedMethodTest(TestCase):
    u"""
    Tests ``cached_method()`` decorator
    """
    class Klass(object):
        @cached_method
        def method1(self, a, b):
            print(u'method1')
            if a == 4: raise TypeError
            if a == 7: raise ValueError
            return a + b
        @cached_method(cached_exceptions=TypeError)
        def method2(self, a, b):
            print(u'method2')
            if a == 4: raise TypeError
            if a == 7: raise ValueError
            return a + b
        @cached_method(cached_exceptions=(TypeError, ValueError))
        def method3(self, a, b):
            print(u'method3')
            if a == 4: raise TypeError
            if a == 7: raise ValueError
            return a + b

    def test_methods_are_cached_separately(self):
        obj = self.Klass()
        with collect_stdout() as output:
            self.assertEqual(obj.method1(2, 3), 5)
            self.assertEqual(obj.method2(2, 3), 5)
            self.assertEqual(obj.method3(2, 3), 5)
        self.assertEqual(output.stdout, u'method1\nmethod2\nmethod3\n')
        with collect_stdout() as output:
            self.assertEqual(obj.method1(2, 3), 5)
            self.assertEqual(obj.method2(2, 3), 5)
            self.assertEqual(obj.method3(2, 3), 5)
        self.assertEqual(output.stdout, u'')

    def test_methods_are_cached_per_instance(self):
        obj1 = self.Klass()
        obj2 = self.Klass()
        with collect_stdout() as output:
            self.assertEqual(obj1.method1(2, 3), 5)
            self.assertEqual(obj1.method2(2, 3), 5)
            self.assertEqual(obj1.method3(2, 3), 5)
        self.assertEqual(output.stdout, u'method1\nmethod2\nmethod3\n')
        with collect_stdout() as output:
            self.assertEqual(obj2.method1(2, 3), 5)
            self.assertEqual(obj2.method2(2, 3), 5)
            self.assertEqual(obj2.method3(2, 3), 5)
        self.assertEqual(output.stdout, u'method1\nmethod2\nmethod3\n')

    def test_cached_exceptions(self):
        obj = self.Klass()
        with collect_stdout() as output:
            with self.assertRaises(TypeError): obj.method2(4, 7)
            with self.assertRaises(TypeError): obj.method3(4, 7)
            with self.assertRaises(ValueError): obj.method3(7, 4)
        self.assertEqual(output.stdout, u'method2\nmethod3\nmethod3\n')
        with collect_stdout() as output:
            with self.assertRaises(TypeError): obj.method2(4, 7)
            with self.assertRaises(TypeError): obj.method3(4, 7)
            with self.assertRaises(ValueError): obj.method3(7, 4)
        self.assertEqual(output.stdout, u'')

    def test_not_cached_exceptions(self):
        obj = self.Klass()
        with collect_stdout() as output:
            with self.assertRaises(TypeError): obj.method1(4, 7)
            with self.assertRaises(ValueError): obj.method1(7, 4)
            with self.assertRaises(ValueError): obj.method2(7, 4)
        self.assertEqual(output.stdout, u'method1\nmethod1\nmethod2\n')
        with collect_stdout() as output:
            with self.assertRaises(TypeError): obj.method1(4, 7)
            with self.assertRaises(ValueError): obj.method1(7, 4)
            with self.assertRaises(ValueError): obj.method2(7, 4)
        self.assertEqual(output.stdout, u'method1\nmethod1\nmethod2\n')
