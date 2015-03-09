# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import models, migrations


class Migration(migrations.Migration):

    dependencies = [
        ('mail', '0003_auto_20150304_0050'),
    ]

    operations = [
        migrations.AlterField(
            model_name='recipient',
            name='message',
            field=models.ForeignKey(to='mail.Message'),
            preserve_default=True,
        ),
        migrations.AlterField(
            model_name='recipient',
            name='remote_id',
            field=models.CharField(help_text='Recipient reference ID set by e-mail transport. Leave blank if not sure.', max_length=255, db_index=True, blank=True),
            preserve_default=True,
        ),
        migrations.AlterIndexTogether(
            name='recipient',
            index_together=set([]),
        ),
    ]
