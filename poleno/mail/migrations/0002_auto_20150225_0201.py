# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import models, migrations


class Migration(migrations.Migration):

    dependencies = [
        ('mail', '0001_initial'),
    ]

    operations = [
        migrations.AlterField(
            model_name='recipient',
            name='message',
            field=models.ForeignKey(to='mail.Message', db_index=False),
            preserve_default=True,
        ),
        migrations.AlterIndexTogether(
            name='message',
            index_together=set([('processed', 'id')]),
        ),
        migrations.AlterIndexTogether(
            name='recipient',
            index_together=set([('message',), ('remote_id',)]),
        ),
    ]
