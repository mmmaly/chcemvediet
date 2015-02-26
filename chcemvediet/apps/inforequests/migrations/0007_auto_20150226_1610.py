# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import models, migrations


class Migration(migrations.Migration):

    dependencies = [
        ('inforequests', '0006_remove_inforequestdraft_content'),
    ]

    operations = [
        migrations.RenameField(
            model_name='inforequestdraft',
            old_name='content_tmp',
            new_name='content',
        ),
    ]
