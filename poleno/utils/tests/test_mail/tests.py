# vim: expandtab
# -*- coding: utf-8 -*-
import os

from django.template import TemplateDoesNotExist
from django.template.loader import render_to_string
from django.test import TestCase
from django.test.utils import override_settings

from poleno.utils.mail import render_mail


settings_overrides = {
    u'TEMPLATE_LOADERS': (u'django.template.loaders.filesystem.Loader',),
    u'TEMPLATE_DIRS': (os.path.abspath(os.path.join(os.path.dirname(__file__), u'templates')),),
}

@override_settings(**settings_overrides)
class RenderMailTest(TestCase):
    u"""
    Tests ``render_mail()`` function. Checks that message subject and body alternatives are
    rendered correctly, that missing templates raise an exception, and that all other arguments are
    passed directly to the message constructor.
    """

    def _get_alternatives(self, msg):
        alternatives = [(u'text/' + msg.content_subtype, msg.body)]
        for content, mimetype in getattr(msg, u'alternatives', []):
            alternatives.append((mimetype, content))
        return alternatives

    def test_message_with_text_and_html(self):
        # existing: 01-first_subject.txt, 01-first_message.txt, 01-first_message.html
        # missing: --
        msg = render_mail(u'01-first')
        alternatives = self._get_alternatives(msg)
        self.assertEqual(alternatives, [
            (u'text/plain', u'First message text with leading and trailing whitespace'),
            (u'text/html', u'<p>\nFirst message HTML with leading and trailing whitespace\n</p>'),
            ])

    def test_message_with_text_only(self):
        # existing: 02-second_subject.txt, 02-second_message.txt
        # missing: 02-second_message.html
        msg = render_mail(u'02-second')
        alternatives = self._get_alternatives(msg)
        self.assertEqual(alternatives, [
            (u'text/plain', u'Second message with only text'),
            ])

    def test_message_with_html_only(self):
        # existing: 03-third_subject.txt, 03-third_message.html
        # missing: 03-third_message.txt
        msg = render_mail(u'03-third')
        alternatives = self._get_alternatives(msg)
        self.assertEqual(alternatives, [
            (u'text/html', u'<p>Third message with only HTML</p>'),
            ])

    def test_message_with_missing_templates(self):
        # existing: 04-fourth_subject.txt
        # missing: 04-fourth_message.txt, 04-fourth_message.html
        with self.assertRaisesMessage(TemplateDoesNotExist, u'04-fourth_message.txt'):
            msg = render_mail(u'04-fourth')

    def test_message_with_missing_subject_template(self):
        # existing: 05-fifth_message.txt
        # missing: 05-fifth_subject.txt, 05-fifth_message.html
        with self.assertRaisesMessage(TemplateDoesNotExist, u'05-fifth_subject.txt'):
            msg = render_mail(u'05-fifth')

    def test_subject_squeezed(self):
        u"""
        Checks that even if the subject template contains leading, trailing or consecutive
        whitespace, tabs or linebreaks, the rendered subject is normalized.
        """
        # Ensure "01-first_subject.txt" contains leading/trailing/consecutive whitespace
        rendered = render_to_string(u'01-first_subject.txt')
        self.assertNotRegexpMatches(rendered, r'^(\S+ )*\S+$')

        msg = render_mail(u'01-first')
        self.assertRegexpMatches(msg.subject, r'^(\S+ )*\S+$')

    def test_body_stripped(self):
        u"""
        Checks that even if the message template contains leading or trailing whitespace, the
        rendered message is stripped.
        """
        # Ensure both "01-first_message.txt" and "01-first_message.html" contain leading/trailing whitespace
        rendered_txt = render_to_string(u'01-first_message.txt')
        rendered_html = render_to_string(u'01-first_message.html')
        self.assertNotEqual(rendered_txt, rendered_txt.strip())
        self.assertNotEqual(rendered_html, rendered_html.strip())

        msg = render_mail(u'01-first')
        alternatives = self._get_alternatives(msg)
        self.assertEqual(alternatives[0][1], alternatives[0][1].strip())
        self.assertEqual(alternatives[1][1], alternatives[1][1].strip())

    def test_message_arguments(self):
        u"""
        Tests arguments passed directly to the message constructor. Checks for ``from_email``,
        ``to``, ``cc``, ``bcc``, ``headers`` and ``attachments`` arguments. Tests them with all
        three message forms: text only, html only and with both text and html parts.
        """
        kwargs = {
            u'from_email': u'test@example.com',
            u'to': [u'first@dest.com', u'second@dest.com'],
            u'cc': [u'John Shmith <john@dest.com>'],
            u'bcc': [u'example@example.com'],
            u'headers': {'Reply-To': 'another@example.com'},
            u'attachments': [(u'filename', u'content', u'application/octet-stream')],
            }

        for template in [u'01-first', u'02-second', u'03-third']:
            msg = render_mail(template, **kwargs)
            self.assertEqual(msg.from_email, kwargs[u'from_email'])
            self.assertEqual(msg.to, kwargs[u'to'])
            self.assertEqual(msg.cc, kwargs[u'cc'])
            self.assertEqual(msg.bcc, kwargs[u'bcc'])
            self.assertEqual(msg.extra_headers, kwargs[u'headers'])
            self.assertEqual(msg.attachments, kwargs[u'attachments'])

    def test_render_mail_with_dictionary(self):
        u"""
        Passes a dictionary to ``render_mail()`` function and checks if templates using it are
        rendered corectly.
        """
        msg = render_mail(u'06-sixth', dictionary={u'variable': 47})
        alternatives = self._get_alternatives(msg)
        self.assertEqual(msg.subject, u'[example.com] Subject with dictionary: 47')
        self.assertEqual(alternatives, [
            (u'text/plain', u'Text message with dictionary: 47'),
            (u'text/html', u'<p>HTML message with dictionary: 47</p>'),
            ])
