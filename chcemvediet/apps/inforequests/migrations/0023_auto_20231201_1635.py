# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import models, migrations
import django.db.models.deletion
import poleno.utils.date
import poleno.utils.misc


class Migration(migrations.Migration):

    dependencies = [
        ('inforequests', '0022_inforequest_published'),
    ]

    operations = [
        migrations.CreateModel(
            name='Feedback',
            fields=[
                ('id', models.AutoField(verbose_name='ID', serialize=False, auto_created=True, primary_key=True)),
                ('content', models.TextField(blank=True)),
                ('created', models.DateTimeField(default=poleno.utils.date.utc_now)),
                ('inforequest', models.ForeignKey(to='inforequests.Inforequest', db_index=False, on_delete=django.db.models.deletion.CASCADE)),
            ],
            options={
                'verbose_name_plural': 'Feedback',
            },
            bases=(poleno.utils.misc.FormatMixin, models.Model),
        ),
        migrations.AlterIndexTogether(
            name='feedback',
            index_together=set([('created', 'id')]),
        ),
    ]
