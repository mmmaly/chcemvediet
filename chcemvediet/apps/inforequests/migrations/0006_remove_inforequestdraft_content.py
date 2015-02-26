# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import models, migrations


class Migration(migrations.Migration):

    dependencies = [
        ('inforequests', '0005_auto_20150226_1557'),
    ]

    operations = [
        migrations.RemoveField(
            model_name='inforequestdraft',
            name='content',
        ),
    ]
