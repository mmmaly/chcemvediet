# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import models, migrations
from django.conf import settings


class Migration(migrations.Migration):

    dependencies = [
        migrations.swappable_dependency(settings.AUTH_USER_MODEL),
        ('invitations', '0002_auto_20150510_1547'),
    ]

    operations = [
        migrations.CreateModel(
            name='InvitationSupply',
            fields=[
                ('id', models.AutoField(verbose_name='ID', serialize=False, auto_created=True, primary_key=True)),
                ('enabled', models.BooleanField(default=True, help_text='Whether the user may send invitations.')),
                ('unlimited', models.BooleanField(default=False, help_text='Whether the user may send an unlimited number of invitations.')),
                ('supply', models.IntegerField(default=0, help_text='The number of invitations the user may send.')),
                ('user', models.OneToOneField(to=settings.AUTH_USER_MODEL, help_text='The user to whom the invitation supply belongs.')),
            ],
            options={
            },
            bases=(models.Model,),
        ),
    ]
