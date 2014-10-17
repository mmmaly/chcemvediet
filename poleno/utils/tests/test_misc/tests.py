# vim: expandtab
# -*- coding: utf-8 -*-
import re
import string
import random

from django.test import TestCase

from poleno.utils.misc import Bunch, random_string, random_readable_string, squeeze

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
        self.assertRegexpMatches(res, r'^([\S]+ )*[\S]+$')

    def test_long_random_text(self):
        sample = u''.join(random.choice(string.printable if random.random() < 0.5 else string.whitespace)
                for i in range(1000))
        res = squeeze(sample)
        self.assertRegexpMatches(res, r'^([\S]+ )*[\S]+$')
