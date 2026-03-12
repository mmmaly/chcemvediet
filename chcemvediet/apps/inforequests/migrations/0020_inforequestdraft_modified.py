# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import models, migrations
import datetime
from datetime import timezone
utc = timezone.utc


class Migration(migrations.Migration):

    dependencies = [
        ('inforequests', '0019_various_indexes'),
    ]

    operations = [
        migrations.AddField(
            model_name='inforequestdraft',
            name='modified',
            field=models.DateTimeField(default=datetime.datetime(2015, 11, 16, 6, 32, 0, 806960, tzinfo=utc), auto_now=True),
            preserve_default=False,
        ),
    ]
