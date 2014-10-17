# vim: expandtab
# -*- coding: utf-8 -*-
import os
from testfixtures import TempDirectory

from django.template.base import TemplateDoesNotExist
from django.template.loader import render_to_string
from django.test import TestCase
from django.test.utils import override_settings

from poleno.utils.translation import translation
from poleno.utils.misc import squeeze


class TranslationLoaderTest(TestCase):
    u"""
    Tests ``TranslationLoader`` template loader. Checks that the loader loads original template
    only if there is no translated template for the active language. If there is a translated
    template for the active languate, the loader loads this translated template. Also tests that an
    exception is raised if there is no original nor translated template.
    """

    def setUp(self):
        self.tempdir = TempDirectory()

        self.settings_override = override_settings(
            LANGUAGES=((u'de', u'Deutsch'), (u'en', u'English'), (u'fr', u'Francais')),
            TEMPLATE_LOADERS=((u'poleno.utils.template.TranslationLoader', u'django.template.loaders.filesystem.Loader'),),
            TEMPLATE_DIRS=(self.tempdir.path,),
            )
        self.settings_override.enable()

        self.tempdir.write(u'first.html', u'(first.html)\n')
        self.tempdir.write(u'first.en.html', u'(first.en.html)\n')
        self.tempdir.write(u'second.de.html', u'(second.de.html)\n')

    def tearDown(self):
        self.settings_override.disable()
        self.tempdir.cleanup()


    def test_translated_template_has_priority(self):
        # Existing: first.html, first.en.html
        with translation(u'en'):
            rendered = squeeze(render_to_string(u'first.html'))
            self.assertEqual(rendered, u'(first.en.html)')

    def test_with_only_translated_template(self):
        # Existing: second.de.html
        # Missing: second.html
        with translation(u'de'):
            rendered = squeeze(render_to_string(u'second.html'))
            self.assertEqual(rendered, u'(second.de.html)')

    def test_with_only_untranslated_template(self):
        # Existing: first.html
        # Missing: first.de.html
        with translation(u'de'):
            rendered = squeeze(render_to_string(u'first.html'))
            self.assertEqual(rendered, u'(first.html)')

    def test_missing_template_raises_exception(self):
        # Missing: second.html, second.en.html
        with self.assertRaises(TemplateDoesNotExist):
            render_to_string(u'second.html')
