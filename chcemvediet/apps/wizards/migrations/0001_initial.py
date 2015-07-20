# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import models, migrations
import jsonfield.fields


class Migration(migrations.Migration):

    dependencies = [
    ]

    operations = [
        migrations.CreateModel(
            name='WizardDraft',
            fields=[
                ('id', models.CharField(max_length=255, serialize=False, primary_key=True)),
                ('step', models.CharField(max_length=32)),
                ('data', jsonfield.fields.JSONField()),
                ('modified', models.DateTimeField(auto_now=True)),
            ],
            options={
            },
            bases=(models.Model,),
        ),
    ]
