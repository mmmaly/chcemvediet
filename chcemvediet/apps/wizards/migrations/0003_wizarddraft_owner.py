# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import models, migrations
import django.db.models.deletion
from django.conf import settings


class Migration(migrations.Migration):

    dependencies = [
        migrations.swappable_dependency(settings.AUTH_USER_MODEL),
        ('wizards', '0002_wizarddraft_step'),
    ]

    operations = [
        migrations.AddField(
            model_name='wizarddraft',
            name='owner',
            field=models.ForeignKey(default=1, to=settings.AUTH_USER_MODEL, on_delete=django.db.models.deletion.CASCADE),
            preserve_default=False,
        ),
    ]
