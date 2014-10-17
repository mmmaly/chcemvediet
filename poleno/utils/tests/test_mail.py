# vim: expandtab
# -*- coding: utf-8 -*-
import os
from testfixtures import TempDirectory

from django.template import TemplateDoesNotExist
from django.template.loader import render_to_string
from django.test import TestCase
from django.test.utils import override_settings

from poleno.utils.mail import render_mail


class RenderMailTest(TestCase):
    u"""
    Tests ``render_mail()`` function. Checks that message subject and body alternatives are
    rendered correctly, that missing templates raise an exception, and that all other arguments are
    passed directly to the message constructor.
    """

    def setUp(self):
        self.tempdir = TempDirectory()

        self.settings_override = override_settings(
            TEMPLATE_LOADERS=(u'django.template.loaders.filesystem.Loader',),
            TEMPLATE_DIRS=(self.tempdir.path,),
            )
        self.settings_override.enable()

        self.tempdir.write(u'first_subject.txt', u'\n\n\t\t\r\r\t\tSubject       with\t\t lots \t  \n\n\t\r\r\n of whitespace\n\n    \n\n  \t')
        self.tempdir.write(u'first_message.txt', u'   \n\n  \t\n\tFirst message text with leading and trailing whitespace   \n     \n\n  \n  ')
        self.tempdir.write(u'first_message.html', u'   \n\n  \t  <p>\nFirst message HTML with leading and trailing whitespace\n</p>\n\n\n\n   ')
        self.tempdir.write(u'second_subject.txt', u'Second subject\n')
        self.tempdir.write(u'second_message.txt', u'Second message with only text\n')
        self.tempdir.write(u'third_subject.txt', u'Third subject\n')
        self.tempdir.write(u'third_message.html', u'<p>Third message with only HTML</p>\n')
        self.tempdir.write(u'fourth_subject.txt', u'Fourth message with no body\n')
        self.tempdir.write(u'fifth_message.txt', u'Fifth message with no subject\n')
        self.tempdir.write(u'sixth_subject.txt', u'Subject with dictionary: {{ variable }}\n')
        self.tempdir.write(u'sixth_message.txt', u'Text message with dictionary: {{ variable }}\n')
        self.tempdir.write(u'sixth_message.html', u'<p>HTML message with dictionary: {{ variable }}</p>\n')

    def tearDown(self):
        self.settings_override.disable()
        self.tempdir.cleanup()


    def _get_alternatives(self, msg):
        alternatives = [(u'text/' + msg.content_subtype, msg.body)]
        for content, mimetype in getattr(msg, u'alternatives', []):
            alternatives.append((mimetype, content))
        return alternatives


    def test_message_with_text_and_html(self):
        # existing: first_subject.txt, first_message.txt, first_message.html
        # missing: --
        msg = render_mail(u'first')
        alternatives = self._get_alternatives(msg)
        self.assertEqual(alternatives, [
            (u'text/plain', u'First message text with leading and trailing whitespace'),
            (u'text/html', u'<p>\nFirst message HTML with leading and trailing whitespace\n</p>'),
            ])

    def test_message_with_text_only(self):
        # existing: second_subject.txt, second_message.txt
        # missing: second_message.html
        msg = render_mail(u'second')
        alternatives = self._get_alternatives(msg)
        self.assertEqual(alternatives, [
            (u'text/plain', u'Second message with only text'),
            ])

    def test_message_with_html_only(self):
        # existing: third_subject.txt, third_message.html
        # missing: third_message.txt
        msg = render_mail(u'third')
        alternatives = self._get_alternatives(msg)
        self.assertEqual(alternatives, [
            (u'text/html', u'<p>Third message with only HTML</p>'),
            ])

    def test_message_with_missing_templates(self):
        # existing: fourth_subject.txt
        # missing: fourth_message.txt, fourth_message.html
        with self.assertRaisesMessage(TemplateDoesNotExist, u'fourth_message.txt'):
            msg = render_mail(u'fourth')

    def test_message_with_missing_subject_template(self):
        # existing: fifth_message.txt
        # missing: fifth_subject.txt, fifth_message.html
        with self.assertRaisesMessage(TemplateDoesNotExist, u'fifth_subject.txt'):
            msg = render_mail(u'fifth')

    def test_subject_squeezed(self):
        u"""
        Checks that even if the subject template contains leading, trailing or consecutive
        whitespace, tabs or linebreaks, the rendered subject is normalized.
        """
        # Ensure "first_subject.txt" contains leading/trailing/consecutive whitespace
        rendered = render_to_string(u'first_subject.txt')
        self.assertNotRegexpMatches(rendered, r'^(\S+ )*\S+$')

        msg = render_mail(u'first')
        self.assertRegexpMatches(msg.subject, r'^(\S+ )*\S+$')

    def test_body_stripped(self):
        u"""
        Checks that even if the message template contains leading or trailing whitespace, the
        rendered message is stripped.
        """
        # Ensure both "first_message.txt" and "first_message.html" contain leading/trailing whitespace
        rendered_txt = render_to_string(u'first_message.txt')
        rendered_html = render_to_string(u'first_message.html')
        self.assertNotEqual(rendered_txt, rendered_txt.strip())
        self.assertNotEqual(rendered_html, rendered_html.strip())

        msg = render_mail(u'first')
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

        for template in [u'first', u'second', u'third']:
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
        msg = render_mail(u'sixth', dictionary={u'variable': 47})
        alternatives = self._get_alternatives(msg)
        self.assertEqual(msg.subject, u'[example.com] Subject with dictionary: 47')
        self.assertEqual(alternatives, [
            (u'text/plain', u'Text message with dictionary: 47'),
            (u'text/html', u'<p>HTML message with dictionary: 47</p>'),
            ])
