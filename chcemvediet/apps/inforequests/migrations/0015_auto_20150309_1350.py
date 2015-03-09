# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import models, migrations


class Migration(migrations.Migration):

    dependencies = [
        ('inforequests', '0014_auto_20150309_1347'),
    ]

    operations = [
        migrations.RemoveField(
            model_name='action',
            name='refusal_reason',
        ),
        migrations.RemoveField(
            model_name='actiondraft',
            name='refusal_reason',
        ),
    ]
