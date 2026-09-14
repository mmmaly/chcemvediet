# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import models, migrations


class Migration(migrations.Migration):

    dependencies = []

    operations = [
        migrations.CreateModel(
            name='CronJobLog',
            fields=[
                (
                    'id',
                    models.AutoField(
                        verbose_name='ID',
                        serialize=False,
                        auto_created=True,
                        primary_key=True,
                    ),
                ),
                ('code', models.CharField(max_length=64, db_index=True)),
                ('start_time', models.DateTimeField(db_index=True)),
                ('end_time', models.DateTimeField(db_index=True)),
                ('is_success', models.BooleanField(default=False)),
                ('message', models.TextField(max_length=1000, blank=True)),
                (
                    'ran_at_time',
                    models.TimeField(
                        db_index=True, null=True, editable=False, blank=True
                    ),
                ),
            ],
        ),
        # The upstream migration used ``index_together`` (removed in Django 5.1). Databases
        # created before django-cron shipped migrations carry these indexes under generated
        # names; that is harmless, Django never needs to touch them again.
        migrations.AddIndex(
            model_name='cronjoblog',
            index=models.Index(fields=['code', 'is_success', 'ran_at_time'], name='django_cron_code_is_succ_idx'),
        ),
        migrations.AddIndex(
            model_name='cronjoblog',
            index=models.Index(fields=['code', 'start_time', 'ran_at_time'], name='django_cron_code_start_r_idx'),
        ),
        migrations.AddIndex(
            model_name='cronjoblog',
            index=models.Index(fields=['code', 'start_time'], name='django_cron_code_start_idx'),
        ),
    ]
