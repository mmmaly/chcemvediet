# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import models, migrations


class Migration(migrations.Migration):

    dependencies = [
        ('attachments', '0001_initial'),
    ]

    operations = [
        migrations.AlterField(
            model_name='attachment',
            name='generic_type',
            field=models.ForeignKey(to='contenttypes.ContentType', db_index=False),
            preserve_default=True,
        ),
        migrations.AlterIndexTogether(
            name='attachment',
            index_together=set([('generic_type', 'generic_id')]),
        ),
    ]
