# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import models, migrations
from poleno.utils.migrations import AlterIndexTogetherStateOnly
import poleno.utils.date


class Migration(migrations.Migration):

    dependencies = [
        ('inforequests', '0008_auto_20150819_1949'),
    ]

    operations = [
        migrations.AddField(
            model_name='action',
            name='created',
            field=models.DateTimeField(default=poleno.utils.date.utc_now, help_text="Point in time used to order branch actions chronologically. By default it's the datetime the action was created. The admin may set the value manually to change actions order in the branch."),
            preserve_default=True,
        ),
        migrations.AddField(
            model_name='action',
            name='deadline_base_date',
            field=models.DateField(help_text='The date the action deadline is relative to. Mandatory for actions that set a deadline. Should be NULL otherwise.', null=True, blank=True),
            preserve_default=True,
        ),
        migrations.AddField(
            model_name='action',
            name='delivered_date',
            field=models.DateField(help_text='The date the action was delivered to the applicant or the obligee. It is optional for applicant actions, mandatory for obligee actions and should be NULL for implicit actions.', null=True, blank=True),
            preserve_default=True,
        ),
        migrations.AddField(
            model_name='action',
            name='legal_date',
            field=models.DateField(help_text='The date the action legally occured. Mandatory for every action.', null=True, blank=True),
            preserve_default=True,
        ),
        migrations.AddField(
            model_name='action',
            name='sent_date',
            field=models.DateField(help_text='The date the action was sent by the applicant or the obligee. It is mandatory for applicant actions, optional for obligee actions and should be NULL for implicit actions.', null=True, blank=True),
            preserve_default=True,
        ),
        migrations.AlterField(
            model_name='action',
            name='effective_date',
            field=models.DateField(help_text="The date at which the action was sent or received. If the action was sent/received by e\u2011mail it's set automatically. If it was sent/received by s\u2011mail it's filled by the applicant.", null=True, blank=True),
            preserve_default=True,
        ),
        AlterIndexTogetherStateOnly(
            name='action',
            index_together=set([('created', 'id')]),
        ),
    ]
