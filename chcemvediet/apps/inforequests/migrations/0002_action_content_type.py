# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import models, migrations


class Migration(migrations.Migration):

    dependencies = [
        ('inforequests', '0001_initial'),
    ]

    operations = [
        migrations.AddField(
            model_name='action',
            name='content_type',
            field=models.SmallIntegerField(default=1, help_text='Mandatory choice action content type. Supported formats are plain text and html code. The html code is assumed to be safe. It is passed to the client without sanitizing. It must be sanitized before saving it here.', choices=[(1, 'Plain Text'), (2, 'HTML')]),
            preserve_default=True,
        ),
    ]
