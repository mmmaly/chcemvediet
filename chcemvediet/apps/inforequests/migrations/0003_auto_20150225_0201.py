# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import models, migrations
import django.db.models.deletion
from django.conf import settings


class Migration(migrations.Migration):

    dependencies = [
        ('inforequests', '0002_auto_20150224_2106'),
    ]

    operations = [
        migrations.AlterField(
            model_name='action',
            name='branch',
            field=models.ForeignKey(to='inforequests.Branch', db_index=False),
            preserve_default=True,
        ),
        migrations.AlterField(
            model_name='action',
            name='email',
            field=models.OneToOneField(null=True, on_delete=django.db.models.deletion.SET_NULL, blank=True, to='mail.Message', db_index=False),
            preserve_default=True,
        ),
        migrations.AlterField(
            model_name='actiondraft',
            name='branch',
            field=models.ForeignKey(blank=True, to='inforequests.Branch', help_text='Must be owned by inforequest if set', null=True, db_index=False),
            preserve_default=True,
        ),
        migrations.AlterField(
            model_name='actiondraft',
            name='inforequest',
            field=models.ForeignKey(to='inforequests.Inforequest', db_index=False),
            preserve_default=True,
        ),
        migrations.AlterField(
            model_name='branch',
            name='advanced_by',
            field=models.ForeignKey(related_name='advanced_to_set', blank=True, to='inforequests.Action', help_text='NULL for main branches. The advancement action the inforequest was advanced by for advanced branches. Every Inforequest must contain exactly one main branch.', null=True, db_index=False),
            preserve_default=True,
        ),
        migrations.AlterField(
            model_name='branch',
            name='historicalobligee',
            field=models.ForeignKey(help_text='Frozen Obligee at the time the Inforequest was submitted or advanced to it.', to='obligees.HistoricalObligee', db_index=False),
            preserve_default=True,
        ),
        migrations.AlterField(
            model_name='branch',
            name='inforequest',
            field=models.ForeignKey(to='inforequests.Inforequest', db_index=False),
            preserve_default=True,
        ),
        migrations.AlterField(
            model_name='branch',
            name='obligee',
            field=models.ForeignKey(help_text='The obligee the inforequest was sent or advanced to.', to='obligees.Obligee', db_index=False),
            preserve_default=True,
        ),
        migrations.AlterField(
            model_name='inforequest',
            name='applicant',
            field=models.ForeignKey(help_text='The inforequest owner, the user who submitted it.', to=settings.AUTH_USER_MODEL, db_index=False),
            preserve_default=True,
        ),
        migrations.AlterField(
            model_name='inforequestdraft',
            name='applicant',
            field=models.ForeignKey(help_text='The draft owner, the future inforequest applicant.', to=settings.AUTH_USER_MODEL, db_index=False),
            preserve_default=True,
        ),
        migrations.AlterField(
            model_name='inforequestdraft',
            name='obligee',
            field=models.ForeignKey(blank=True, to='obligees.Obligee', help_text='The obligee the inforequest will be sent to, if the user has already set it.', null=True, db_index=False),
            preserve_default=True,
        ),
        migrations.AlterField(
            model_name='inforequestemail',
            name='email',
            field=models.ForeignKey(to='mail.Message', db_index=False),
            preserve_default=True,
        ),
        migrations.AlterField(
            model_name='inforequestemail',
            name='inforequest',
            field=models.ForeignKey(to='inforequests.Inforequest', db_index=False),
            preserve_default=True,
        ),
        migrations.AlterIndexTogether(
            name='action',
            index_together=set([('email',), ('effective_date', 'id'), ('branch',)]),
        ),
        migrations.AlterIndexTogether(
            name='actiondraft',
            index_together=set([('branch',), ('inforequest',)]),
        ),
        migrations.AlterIndexTogether(
            name='branch',
            index_together=set([('inforequest', 'advanced_by'), ('historicalobligee',), ('advanced_by', 'inforequest'), ('obligee',)]),
        ),
        migrations.AlterIndexTogether(
            name='inforequest',
            index_together=set([('submission_date', 'id'), ('applicant',), ('unique_email',)]),
        ),
        migrations.AlterIndexTogether(
            name='inforequestdraft',
            index_together=set([('obligee',), ('applicant',)]),
        ),
        migrations.AlterIndexTogether(
            name='inforequestemail',
            index_together=set([('inforequest', 'email'), ('email', 'inforequest'), ('type', 'inforequest')]),
        ),
    ]
