# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import models, migrations
import jsonfield.fields


class Migration(migrations.Migration):

    dependencies = [
        ('inforequests', '0003_auto_20150225_0201'),
    ]

    operations = [
        migrations.AddField(
            model_name='inforequestdraft',
            name='content_tmp',
            field=jsonfield.fields.JSONField(default=(), blank=True),
            preserve_default=True,
        ),
    ]
