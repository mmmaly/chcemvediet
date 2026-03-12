# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import models, migrations
import datetime
from datetime import timezone
utc = timezone.utc


class Migration(migrations.Migration):

    dependencies = [
        ('mail', '0001_initial'),
    ]

    operations = [
        migrations.AddField(
            model_name='message',
            name='created',
            field=models.DateTimeField(default=datetime.datetime(2015, 9, 7, 17, 16, 53, 979507, tzinfo=utc), help_text='Date and time the message object was created,', auto_now_add=True),
            preserve_default=False,
        ),
    ]
