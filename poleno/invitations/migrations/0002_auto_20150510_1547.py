# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import models, migrations
from django.conf import settings


class Migration(migrations.Migration):

    dependencies = [
        ('invitations', '0001_initial'),
    ]

    operations = [
        migrations.AlterField(
            model_name='invitation',
            name='accepted',
            field=models.DateTimeField(help_text='Date and time the invitation was accepted and the invitee registered himself. NULL if the invitation was not accepted yet.', null=True, blank=True),
            preserve_default=True,
        ),
        migrations.AlterField(
            model_name='invitation',
            name='invitee',
            field=models.OneToOneField(related_name='invited_with', null=True, blank=True, to=settings.AUTH_USER_MODEL, help_text='The user who was invited after he accepts the invitation and registers himself. NULL for pending and expired invitations.'),
            preserve_default=True,
        ),
    ]
