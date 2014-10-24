# vim: expandtab
# -*- coding: utf-8 -*-
from testfixtures import TempDirectory

from django import forms
from django.core.files.base import ContentFile
from django.template import Context, Template
from django.contrib.auth.models import User
from django.test import TestCase
from django.test.utils import override_settings

from ..models import Attachment
from ..forms import AttachmentsField

class AttachmentsFieldTest(TestCase):
    u"""
    Tests ``AttachmentsField`` form field with ``AttachmentsWidget`` form widget.
    """

    class AttachmentsFieldForm(forms.Form):
        attachments = AttachmentsField(
                upload_url_func = lambda: u'/upload/',
                download_url_func = lambda a: u'/download/%s/' % a.pk,
                )

        def __init__(self, *args, **kwargs):
            attached_to = kwargs.pop(u'attached_to')
            required = kwargs.pop(u'required', True)
            super(AttachmentsFieldTest.AttachmentsFieldForm, self).__init__(*args, **kwargs)
            self.fields[u'attachments'].attached_to = attached_to
            self.fields[u'attachments'].required = required


    def setUp(self):
        self.tempdir = TempDirectory()

        self.settings_override = override_settings(
            MEDIA_ROOT=self.tempdir.path,
            PASSWORD_HASHERS=(u'django.contrib.auth.hashers.MD5PasswordHasher',),
            )
        self.settings_override.enable()


        self.user1 = User.objects.create_user(u'john', u'lennon@thebeatles.com', u'johnpassword')
        self.attachment1a = Attachment.objects.create(generic_object=self.user1, file=ContentFile(u'content1a'), name=u'filename1a', content_type=u'text/plain')
        self.attachment1b = Attachment.objects.create(generic_object=self.user1, file=ContentFile(u'content1b'), name=u'filename1b', content_type=u'text/plain')
        self.attachment1c = Attachment.objects.create(generic_object=self.user1, file=ContentFile(u'content1c'), name=u'filename1c', content_type=u'text/plain')

        self.user2 = User.objects.create_user(u'smith', u'agent@smith.com', u'big_secret')
        self.attachment2 = Attachment.objects.create(generic_object=self.user2, file=ContentFile(u'content2'), name=u'filename2', content_type=u'text/plain')


    def tearDown(self):
        self.settings_override.disable()
        self.tempdir.cleanup()


    def _render(self, template, **context):
        return Template(template).render(Context(context))


    def test_new_form(self):
        form = self.AttachmentsFieldForm(attached_to=self.user1)
        rendered = self._render(u'{{ form }}', form=form)
        self.assertInHTML(u'<label for="id_attachments">Attachments:</label>', rendered)
        self.assertInHTML(u'<input id="id_attachments" name="attachments" type="text" value=",,">', rendered)
        self.assertInHTML(u"""
                <span class="btn btn-default btn-file">Browse
                  <input class="fileupload" type="file" name="files" multiple="multiple" data-url="/upload/"
                         data-field="#id_attachments" data-target="#attachments-target">
                </span>
                """, rendered)

    def test_submitted_form_with_no_attachments_but_required(self):
        attachments = u',,,,'
        form = self.AttachmentsFieldForm({u'attachments': attachments}, attached_to=self.user1)
        self.assertFalse(form.is_valid())
        rendered = self._render(u'{{ form }}', form=form)
        self.assertInHTML(u'<ul class="errorlist"><li>This field is required.</li></ul>', rendered)
        self.assertInHTML(u'<input id="id_attachments" name="attachments" type="text" value=",,">', rendered)

    def test_submitted_form_with_no_attachments_but_not_required(self):
        attachments = u',,,,'
        form = self.AttachmentsFieldForm({u'attachments': attachments}, attached_to=self.user1, required=False)
        self.assertTrue(form.is_valid())
        rendered = self._render(u'{{ form }}', form=form)
        self.assertInHTML(u'<li>This field is required.</li>', rendered, count=0)
        self.assertInHTML(u'<input id="id_attachments" name="attachments" type="text" value=",,">', rendered)

    def test_submitted_form_with_one_attachment(self):
        attachments = u',,%s,,' % self.attachment1a.pk
        form = self.AttachmentsFieldForm({u'attachments': attachments}, attached_to=self.user1)
        self.assertTrue(form.is_valid())
        rendered = self._render(u'{{ form }}', form=form)
        self.assertInHTML(u'<li>This field is required.</li>', rendered, count=0)
        self.assertInHTML(u'<input id="id_attachments" name="attachments" type="text" value=",%s,">' % self.attachment1a.pk, rendered)
        self.assertInHTML(u'<a href="/download/%s/">filename1a</a>' % self.attachment1a.pk, rendered)

    def test_submitted_form_with_multiple_attachments(self):
        attachments = u'%s,%s,%s' % (self.attachment1a.pk, self.attachment1b.pk, self.attachment1c.pk)
        form = self.AttachmentsFieldForm({u'attachments': attachments}, attached_to=self.user1)
        self.assertTrue(form.is_valid())
        rendered = self._render(u'{{ form }}', form=form)
        self.assertInHTML(u'<input id="id_attachments" name="attachments" type="text" value=",%s,">' % attachments, rendered)
        self.assertInHTML(u'<a href="/download/%s/">filename1a</a>' % self.attachment1a.pk, rendered)
        self.assertInHTML(u'<a href="/download/%s/">filename1b</a>' % self.attachment1b.pk, rendered)
        self.assertInHTML(u'<a href="/download/%s/">filename1c</a>' % self.attachment1c.pk, rendered)

    def test_submitted_form_with_forbidden_attachment(self):
        attachments = u',,%s,,' % self.attachment2.pk
        form = self.AttachmentsFieldForm({u'attachments': attachments}, attached_to=self.user1)
        self.assertFalse(form.is_valid())
        rendered = self._render(u'{{ form }}', form=form)
        self.assertInHTML(u'<ul class="errorlist"><li>Invalid attachments.</li></ul>', rendered)
        self.assertInHTML(u'<input id="id_attachments" name="attachments" type="text" value=",,">', rendered)

    def test_submitted_form_with_invalid_argument(self):
        attachments = u'invalid'
        form = self.AttachmentsFieldForm({u'attachments': attachments}, attached_to=self.user1)
        self.assertFalse(form.is_valid())
        rendered = self._render(u'{{ form }}', form=form)
        self.assertInHTML(u'<ul class="errorlist"><li>Invalid attachments.</li></ul>', rendered)
        self.assertInHTML(u'<input id="id_attachments" name="attachments" type="text" value=",,">', rendered)

    def test_form_with_attached_to_as_list(self):
        attachments = u'%s,%s' % (self.attachment1b.pk, self.attachment2.pk)
        form = self.AttachmentsFieldForm({u'attachments': attachments}, attached_to=[self.user1, self.user2])
        self.assertTrue(form.is_valid())
        rendered = self._render(u'{{ form }}', form=form)
        self.assertInHTML(u'<input id="id_attachments" name="attachments" type="text" value=",%s,">' % attachments, rendered)
        self.assertInHTML(u'<a href="/download/%s/">filename1b</a>' % self.attachment1b.pk, rendered)
        self.assertInHTML(u'<a href="/download/%s/">filename2</a>' % self.attachment2.pk, rendered)

    def test_attachments_field_properties(self):
        u"""
        Checks that if we change ``upload_url_func`` and ``download_url_func`` field properties,
        the field widget properties are changed as well.
        """
        field = AttachmentsField()
        self.assertIsNone(field.attached_to)
        self.assertIsNone(field.upload_url_func)
        self.assertIsNone(field.download_url_func)
        self.assertIsNone(field.widget.upload_url_func)
        self.assertIsNone(field.widget.download_url_func)

        field.attached_to = self.user1
        field.upload_url_func = lambda: u'/upload/'
        field.download_url_func = lambda a: u'/download/%s/' % a.pk
        self.assertEqual(field.attached_to, self.user1)
        self.assertEqual(field.upload_url_func(), u'/upload/')
        self.assertEqual(field.download_url_func(self.attachment2), u'/download/%s/' % self.attachment2.pk)
        self.assertEqual(field.widget.upload_url_func(), u'/upload/')
        self.assertEqual(field.widget.download_url_func(self.attachment2), u'/download/%s/' % self.attachment2.pk)
