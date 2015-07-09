# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import models, migrations


class Migration(migrations.Migration):

    dependencies = [
        ('invitations', '0004_invitationsupply_data'),
    ]

    operations = [
        migrations.AlterModelOptions(
            name='invitationsupply',
            options={'verbose_name_plural': 'invitation supplies'},
        ),
    ]
