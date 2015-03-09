# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import models, migrations
import django.db.models.deletion
from django.conf import settings


class Migration(migrations.Migration):

    dependencies = [
        ('inforequests', '0016_auto_20150309_1351'),
    ]

    operations = [
        migrations.AlterField(
            model_name='action',
            name='branch',
            field=models.ForeignKey(to='inforequests.Branch'),
            preserve_default=True,
        ),
        migrations.AlterField(
            model_name='action',
            name='email',
            field=models.OneToOneField(null=True, on_delete=django.db.models.deletion.SET_NULL, blank=True, to='mail.Message'),
            preserve_default=True,
        ),
        migrations.AlterField(
            model_name='actiondraft',
            name='branch',
            field=models.ForeignKey(blank=True, to='inforequests.Branch', help_text='Must be owned by inforequest if set', null=True),
            preserve_default=True,
        ),
        migrations.AlterField(
            model_name='actiondraft',
            name='inforequest',
            field=models.ForeignKey(to='inforequests.Inforequest'),
            preserve_default=True,
        ),
        migrations.AlterField(
            model_name='branch',
            name='historicalobligee',
            field=models.ForeignKey(help_text='Frozen Obligee at the time the Inforequest was submitted or advanced to it.', to='obligees.HistoricalObligee'),
            preserve_default=True,
        ),
        migrations.AlterField(
            model_name='branch',
            name='obligee',
            field=models.ForeignKey(help_text='The obligee the inforequest was sent or advanced to.', to='obligees.Obligee'),
            preserve_default=True,
        ),
        migrations.AlterField(
            model_name='inforequest',
            name='applicant',
            field=models.ForeignKey(help_text='The inforequest owner, the user who submitted it.', to=settings.AUTH_USER_MODEL),
            preserve_default=True,
        ),
        migrations.AlterField(
            model_name='inforequest',
            name='unique_email',
            field=models.EmailField(help_text='Unique email address used to identify which obligee email belongs to which inforequest. If the inforequest was advanced to other obligees, the same email address is used for communication with all such obligees, as there is no way to tell them to send their response to a different email address.', unique=True, max_length=255, db_index=True),
            preserve_default=True,
        ),
        migrations.AlterField(
            model_name='inforequestdraft',
            name='applicant',
            field=models.ForeignKey(help_text='The draft owner, the future inforequest applicant.', to=settings.AUTH_USER_MODEL),
            preserve_default=True,
        ),
        migrations.AlterField(
            model_name='inforequestdraft',
            name='obligee',
            field=models.ForeignKey(blank=True, to='obligees.Obligee', help_text='The obligee the inforequest will be sent to, if the user has already set it.', null=True),
            preserve_default=True,
        ),
        migrations.AlterIndexTogether(
            name='action',
            index_together=set([('effective_date', 'id')]),
        ),
        migrations.AlterIndexTogether(
            name='actiondraft',
            index_together=set([]),
        ),
        migrations.AlterIndexTogether(
            name='branch',
            index_together=set([('inforequest', 'advanced_by'), ('advanced_by', 'inforequest')]),
        ),
        migrations.AlterIndexTogether(
            name='inforequest',
            index_together=set([('submission_date', 'id')]),
        ),
        migrations.AlterIndexTogether(
            name='inforequestdraft',
            index_together=set([]),
        ),
    ]
