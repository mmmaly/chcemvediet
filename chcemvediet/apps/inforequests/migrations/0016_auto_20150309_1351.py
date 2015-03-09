# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import models, migrations


class Migration(migrations.Migration):

    dependencies = [
        ('inforequests', '0015_auto_20150309_1350'),
    ]

    operations = [
        migrations.RenameField(
            model_name='action',
            old_name='refusal_reason2',
            new_name='refusal_reason',
        ),
        migrations.RenameField(
            model_name='actiondraft',
            old_name='refusal_reason2',
            new_name='refusal_reason',
        ),
    ]
