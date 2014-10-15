# vim: expandtab
# -*- coding: utf-8 -*-
from django.test import TestCase
from django.utils.translation import get_language, activate

from poleno.utils.translation import translation

class TranslationTest(TestCase):
    u"""
    Tests ``translation()`` context manger.
    """
    def setUp(self):
        self.original_language = get_language()

    def tearDown(self):
        activate(self.original_language)

    def test_normal_flow(self):
        u"""
        Tests that ``translation(lang)`` changes the selected language within the ``with``
        statement and restores it afterwards.
        """
        original = get_language()
        with translation(u'de'):
            self.assertEqual(get_language(), u'de')
            with translation(u'sk'):
                self.assertEqual(get_language(), u'sk')
            self.assertEqual(get_language(), u'de')
        self.assertEqual(get_language(), original)

    def test_exception(self):
        u"""
        Tests that ``translation(lang)`` restores the language even if an exception is raised
        within the ``with`` statement.
        """
        original = get_language()
        try:
            with translation(u'de'):
                self.assertEqual(get_language(), u'de')
                try:
                    with translation(u'sk'):
                        self.assertEqual(get_language(), u'sk')
                        raise ValueError
                finally:
                    self.assertEqual(get_language(), u'de') # pragma: no branch
        except ValueError:
            pass
        self.assertEqual(get_language(), original)
