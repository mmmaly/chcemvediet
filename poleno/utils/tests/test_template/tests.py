# vim: expandtab
# -*- coding: utf-8 -*-
import os

from django.template.base import TemplateDoesNotExist
from django.template.loader import render_to_string
from django.test import TestCase

from poleno.utils.translation import translation
from poleno.utils.misc import squeeze

class TranslationLoaderTest(TestCase):
    u"""
    Tests ``TranslationLoader``.
    """

    def test_loaded_template(self):
        u"""
        Tests that ``TranslationLoader`` loads original template only if there is no translated
        template for the active language. If there is a translated template for the active
        languate, the loader loads this translated template. Also tests that an exception is raised
        if there is no original nor translated template.
        """
        lang = ((u'de', u'Deutsch'), (u'en', u'English'), (u'fr', u'Francais'))
        loader = ((u'poleno.utils.template.TranslationLoader', u'django.template.loaders.filesystem.Loader'),)
        dirs = (os.path.abspath(os.path.join(os.path.dirname(__file__), u'templates')),)
        with self.settings(LANGUAGES=lang, TEMPLATE_LOADERS=loader, TEMPLATE_DIRS=dirs):
            with translation(u'en'):
                # Translated "first.en.html" has priority over "first.html".
                rendered = squeeze(render_to_string(u'first.html'))
                self.assertEqual(rendered, u'(first.en.html)')
                # There is neither "second.en.html" nor "second.html"
                with self.assertRaises(TemplateDoesNotExist):
                    rendered = squeeze(render_to_string(u'second.html'))
            with translation(u'de'):
                # There is no "first.de.html" we have only "first.html".
                rendered = squeeze(render_to_string(u'first.html'))
                self.assertEqual(rendered, u'(first.html)')
                # There is only "second.de.html" and no "second.html"
                rendered = squeeze(render_to_string(u'second.html'))
                self.assertEqual(rendered, u'(second.de.html)')
