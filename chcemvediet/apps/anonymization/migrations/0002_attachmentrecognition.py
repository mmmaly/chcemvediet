# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import models, migrations
import django.db.models.deletion


class Migration(migrations.Migration):

    dependencies = [
        ('attachments', '0004_name_sanitization'),
        ('anonymization', '0001_attachmentnormalization'),
    ]

    operations = [
        migrations.CreateModel(
            name='AttachmentRecognition',
            fields=[
                ('id', models.AutoField(verbose_name='ID', serialize=False, auto_created=True, primary_key=True)),
                ('successful', models.BooleanField(default=False, help_text='True if recognition has succeeded, False otherwise.')),
                ('file', models.FileField(help_text='Empty filename if recognition failed.', max_length=255, upload_to='attachment_recognitions', blank=True)),
                ('name', models.CharField(help_text='Attachment recognition file name, e.g. "document.odt". Extension automatically adjusted when creating a new object. Empty, if file.name is empty.', max_length=255, blank=True)),
                ('content_type', models.CharField(help_text='Attachment recognition content type, e.g. "application/vnd.oasis.opendocument.text". The value may be specified even if recognition failed.', max_length=255, null=True)),
                ('created', models.DateTimeField(help_text='Date and time the attachment was recognized. Leave blank for current time.', blank=True)),
                ('size', models.IntegerField(help_text='Attachment recognition file size in bytes. NULL if file is NULL. Automatically computed when creating a new object.', null=True, blank=True)),
                ('debug', models.TextField(help_text='Debug message from recognition.', blank=True)),
                ('attachment', models.ForeignKey(to='attachments.Attachment', on_delete=django.db.models.deletion.CASCADE)),
            ],
            options={
            },
            bases=(models.Model,),
        ),
    ]
