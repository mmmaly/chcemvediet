# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import models, migrations


class Migration(migrations.Migration):

    dependencies = [
        ('inforequests', '0011_auto_20150226_1810'),
    ]

    operations = [
        migrations.AlterModelOptions(
            name='action',
            options={},
        ),
        migrations.AlterModelOptions(
            name='actiondraft',
            options={},
        ),
        migrations.AlterModelOptions(
            name='branch',
            options={'verbose_name_plural': 'Branches'},
        ),
        migrations.AlterModelOptions(
            name='inforequest',
            options={},
        ),
        migrations.AlterModelOptions(
            name='inforequestdraft',
            options={},
        ),
    ]
