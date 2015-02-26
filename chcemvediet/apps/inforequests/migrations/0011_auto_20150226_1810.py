# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import models, migrations


class Migration(migrations.Migration):

    dependencies = [
        ('inforequests', '0010_remove_inforequestdraft_subject'),
    ]

    operations = [
        migrations.RenameField(
            model_name='inforequestdraft',
            old_name='subject_tmp',
            new_name='subject',
        ),
    ]
