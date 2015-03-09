# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import models, migrations


class Migration(migrations.Migration):

    dependencies = [
        ('contenttypes', '0001_initial'),
    ]

    operations = [
        migrations.CreateModel(
            name='Attachment',
            fields=[
                ('id', models.AutoField(verbose_name='ID', serialize=False, auto_created=True, primary_key=True)),
                ('generic_id', models.CharField(max_length=255)),
                ('file', models.FileField(max_length=255, upload_to='attachments')),
                ('name', models.CharField(help_text='Attachment file name, e.g. "document.pdf". The value does not have to be a valid filename. It may be set by the user.', max_length=255)),
                ('content_type', models.CharField(help_text='Attachment content type, e.g. "application/pdf". The value does not have to be a valid content type. It may be set by the user.', max_length=255)),
                ('created', models.DateTimeField(help_text='Date and time the attachment was uploaded or received by an email. Leave blank for current time.', blank=True)),
                ('size', models.IntegerField(help_text='Attachment file size in bytes. Automatically computed when creating a new object.', blank=True)),
                ('generic_type', models.ForeignKey(to='contenttypes.ContentType', db_index=False)),
            ],
            options={
            },
            bases=(models.Model,),
        ),
        migrations.AlterIndexTogether(
            name='attachment',
            index_together=set([('generic_type', 'generic_id')]),
        ),
    ]
