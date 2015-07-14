# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import models, migrations


class Migration(migrations.Migration):

    dependencies = [
        ('inforequests', '0004_action_file_number'),
    ]

    operations = [
        migrations.AddField(
            model_name='actiondraft',
            name='file_number',
            field=models.CharField(help_text='Optional for obligee actions. Should be empty for other actions.', max_length=255, blank=True),
            preserve_default=True,
        ),
    ]
