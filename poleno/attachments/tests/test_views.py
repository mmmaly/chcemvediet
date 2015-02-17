# vim: expandtab
# -*- coding: utf-8 -*-
import time
import datetime
import json
from testfixtures import TempDirectory

from django.core.files.base import ContentFile
from django.conf.urls import patterns, url
from django.http import HttpResponseNotModified, FileResponse, JsonResponse
from django.contrib.auth.models import User
from django.utils.http import http_date
from django.test import TestCase
from django.test.utils import override_settings

from poleno.utils.date import utc_now

from ..models import Attachment
from ..views import upload, download

class AttachmentViewsTest(TestCase):
    u"""
    Tests ``upload()`` and ``download()`` views.
    """
    def upload_view(request):
        user = User.objects.first()
        return upload(request, user, lambda a: u'/download/%s/' % a.pk)

    def download_view(request):
        attachment = Attachment.objects.first()
        return download(request, attachment)

    urls = patterns(u'',
        url(r'^upload/$', upload_view),
        url(r'^download/$', download_view),
        )


    def setUp(self):
        self.tempdir = TempDirectory()

        self.settings_override = override_settings(
            MEDIA_ROOT=self.tempdir.path,
            PASSWORD_HASHERS=(u'django.contrib.auth.hashers.MD5PasswordHasher',),
            )
        self.settings_override.enable()

        self.user = User.objects.create_user(u'john', u'lennon@thebeatles.com', u'johnpassword')
        self.user2 = User.objects.create_user(u'smith', u'agent@smith.com', u'big_secret')

    def tearDown(self):
        self.settings_override.disable()
        self.tempdir.cleanup()


    def test_download(self):
        obj = Attachment.objects.create(
                generic_object=self.user,
                file=ContentFile(u'content'),
                name=u'filename',
                content_type=u'text/plain',
                )
        response = self.client.get(u'/download/')
        self.assertIs(type(response), FileResponse)
        self.assertEqual(response.status_code, 200)
        self.assertEqual(u''.join(response.streaming_content), u'content')

    def test_download_with_if_modified_since_with_unmodified_file(self):
        obj = Attachment.objects.create(
                generic_object=self.user,
                file=ContentFile(u'content'),
                name=u'filename',
                content_type=u'text/plain',
                )
        response = self.client.get(u'/download/', HTTP_IF_MODIFIED_SINCE=http_date(time.time()))
        self.assertIs(type(response), HttpResponseNotModified)
        self.assertEqual(response.status_code, 304)
        self.assertEqual(response.content, u'')

    def test_download_with_if_modified_since_with_modified_file(self):
        obj = Attachment.objects.create(
                generic_object=self.user,
                file=ContentFile(u'content'),
                name=u'filename',
                content_type=u'text/plain',
                )
        response = self.client.get(u'/download/', HTTP_IF_MODIFIED_SINCE=http_date(time.time()-10))
        self.assertIs(type(response), FileResponse)
        self.assertEqual(response.status_code, 200)
        self.assertEqual(u''.join(response.streaming_content), u'content')

    def test_upload(self):
        response = self.client.post(u'/upload/', {u'files': ContentFile(u'uploaded', name=u'filename')})
        self.assertIs(type(response), JsonResponse)
        self.assertEqual(response.status_code, 200)

        self.assertEqual(json.loads(response.content), {u'files': [
            {u'url': u'/download/1/', u'pk': 1, u'name': u'filename', u'size': 8},
            ]})
        obj = Attachment.objects.get(pk=1)
        self.assertEqual(obj.generic_object, self.user)
        self.assertEqual(obj.name, u'filename')
        self.assertEqual(obj.content_type, u'application/octet-stream')
        self.assertAlmostEqual(obj.created, utc_now(), delta=datetime.timedelta(seconds=10))
        self.assertEqual(obj.size, 8)
        self.assertEqual(obj.content, u'uploaded')

    def test_upload_multiple_files(self):
        response = self.client.post(u'/upload/', {u'files': [
            ContentFile(u'uploaded', name=u'filename'),
            ContentFile(u'uploaded2', name=u'filename2'),
            ContentFile(u'uploaded3', name=u'filename3'),
            ]})
        self.assertIs(type(response), JsonResponse)
        self.assertEqual(response.status_code, 200)

        self.assertEqual(json.loads(response.content), {u'files': [
            {u'url': u'/download/1/', u'pk': 1, u'name': u'filename', u'size': 8},
            {u'url': u'/download/2/', u'pk': 2, u'name': u'filename2', u'size': 9},
            {u'url': u'/download/3/', u'pk': 3, u'name': u'filename3', u'size': 9},
            ]})
        obj = Attachment.objects.get(pk=1)
        self.assertEqual(obj.content, u'uploaded')
        obj = Attachment.objects.get(pk=2)
        self.assertEqual(obj.content, u'uploaded2')
        obj = Attachment.objects.get(pk=3)
        self.assertEqual(obj.content, u'uploaded3')
