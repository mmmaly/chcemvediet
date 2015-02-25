# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import models, migrations


class Migration(migrations.Migration):

    dependencies = [
        ('obligees', '0001_initial'),
    ]

    operations = [
        migrations.AlterField(
            model_name='historicalobligee',
            name='slug',
            field=models.SlugField(help_text='Slug for full-text search. Automaticly computed whenever creating a new object or changing its name. Any user defined value is replaced.', max_length=255, db_index=False),
            preserve_default=True,
        ),
        migrations.AlterField(
            model_name='obligee',
            name='slug',
            field=models.SlugField(help_text='Slug for full-text search. Automaticly computed whenever creating a new object or changing its name. Any user defined value is replaced.', max_length=255, db_index=False),
            preserve_default=True,
        ),
        migrations.AlterIndexTogether(
            name='obligee',
            index_together=set([('name', 'id')]),
        ),
    ]
