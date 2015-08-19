# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import models, migrations


class Migration(migrations.Migration):

    dependencies = [
        ('inforequests', '0007_action_no_reason_data'),
    ]

    operations = [
        migrations.RemoveField(
            model_name='actiondraft',
            name='branch',
        ),
        migrations.RemoveField(
            model_name='actiondraft',
            name='inforequest',
        ),
        migrations.RemoveField(
            model_name='actiondraft',
            name='obligee_set',
        ),
        migrations.DeleteModel(
            name='ActionDraft',
        ),
    ]
