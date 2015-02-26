# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import models, migrations
import jsonfield.fields


class Migration(migrations.Migration):

    dependencies = [
        ('inforequests', '0007_auto_20150226_1610'),
    ]

    operations = [
        migrations.AddField(
            model_name='inforequestdraft',
            name='subject_tmp',
            field=jsonfield.fields.JSONField(default=(), blank=True),
            preserve_default=True,
        ),
    ]
