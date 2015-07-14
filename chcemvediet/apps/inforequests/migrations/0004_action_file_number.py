# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import models, migrations


class Migration(migrations.Migration):

    dependencies = [
        ('inforequests', '0003_auto_20150714_1103'),
    ]

    operations = [
        migrations.AddField(
            model_name='action',
            name='file_number',
            field=models.CharField(help_text='A file number assigned to the action by the obligee. Usually only obligee actions have it. However, if we know tha obligee assigned a file number to an applicant action, we should keep it here as well. The file number is not mandatory.', max_length=255, blank=True),
            preserve_default=True,
        ),
    ]
