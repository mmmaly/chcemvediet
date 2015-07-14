# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import models, migrations


class Migration(migrations.Migration):

    dependencies = [
        ('inforequests', '0002_action_content_type'),
    ]

    operations = [
        migrations.AddField(
            model_name='inforequest',
            name='content',
            field=models.TextField(help_text='Part of the inforequest content written by the applicant. It does not include formal texts added by us. It should only contain an exact definition of the requested information. It may be formatted into multiple paragraphs using line feeds.', blank=True),
            preserve_default=True,
        ),
        migrations.AddField(
            model_name='inforequest',
            name='subject',
            field=models.CharField(help_text='Part of the inforequest subject written by the applicant. It does not include formal prefix added by us. It should only contain a short (few words) definition of the requested information.', max_length=255, blank=True),
            preserve_default=True,
        ),
    ]
