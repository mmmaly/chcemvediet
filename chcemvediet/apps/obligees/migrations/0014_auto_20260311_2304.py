# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import migrations, models
import django.db.models.deletion
from django.conf import settings


class Migration(migrations.Migration):

    dependencies = [
        ('geounits', '0002_neighbourhood_cadastre'),
        ('obligees', '0013_auto_20151213_0838'),
    ]

    operations = [
        migrations.RemoveField(
            model_name='historicalobligee',
            name='iczsj_id',
        ),
        migrations.AddField(
            model_name='historicalobligee',
            name='history_change_reason',
            field=models.CharField(max_length=100, null=True),
        ),
        migrations.AddField(
            model_name='historicalobligee',
            name='iczsj',
            field=models.ForeignKey(related_name='+', on_delete=django.db.models.deletion.DO_NOTHING, db_constraint=False, blank=True, to='geounits.Neighbourhood', null=True),
        ),
        migrations.AlterField(
            model_name='historicalobligee',
            name='gender',
            field=models.SmallIntegerField(help_text='Obligee name grammar gender.', choices=[(1, 'obligees:Obligee:gender:MASCULINE'), (2, 'obligees:Obligee:gender:FEMININE'), (3, 'obligees:Obligee:gender:NEUTER'), (4, 'obligees:Obligee:gender:PLURALE')]),
        ),
        migrations.AlterField(
            model_name='historicalobligee',
            name='history_user',
            field=models.ForeignKey(related_name='+', on_delete=django.db.models.deletion.SET_NULL, to=settings.AUTH_USER_MODEL, null=True),
        ),
        migrations.AlterField(
            model_name='historicalobligee',
            name='status',
            field=models.SmallIntegerField(help_text='"Pending" for obligees that exist and accept inforequests; "Dissolved" for obligees that do not exist any more and no further inforequests may be submitted to them.', choices=[(1, 'obligees:Obligee:status:PENDING'), (2, 'obligees:Obligee:status:DISSOLVED')]),
        ),
        migrations.AlterField(
            model_name='historicalobligee',
            name='type',
            field=models.SmallIntegerField(help_text='Obligee type according to \xa72. Obligees defined in section 3 are obliged to disclose some information only.', choices=[(1, 'obligees:Obligee:type:SECTION_1'), (2, 'obligees:Obligee:type:SECTION_2'), (3, 'obligees:Obligee:type:SECTION_3'), (4, 'obligees:Obligee:type:SECTION_4')]),
        ),
        migrations.AlterField(
            model_name='obligee',
            name='gender',
            field=models.SmallIntegerField(help_text='Obligee name grammar gender.', choices=[(1, 'obligees:Obligee:gender:MASCULINE'), (2, 'obligees:Obligee:gender:FEMININE'), (3, 'obligees:Obligee:gender:NEUTER'), (4, 'obligees:Obligee:gender:PLURALE')]),
        ),
        migrations.AlterField(
            model_name='obligee',
            name='status',
            field=models.SmallIntegerField(help_text='"Pending" for obligees that exist and accept inforequests; "Dissolved" for obligees that do not exist any more and no further inforequests may be submitted to them.', choices=[(1, 'obligees:Obligee:status:PENDING'), (2, 'obligees:Obligee:status:DISSOLVED')]),
        ),
        migrations.AlterField(
            model_name='obligee',
            name='type',
            field=models.SmallIntegerField(help_text='Obligee type according to \xa72. Obligees defined in section 3 are obliged to disclose some information only.', choices=[(1, 'obligees:Obligee:type:SECTION_1'), (2, 'obligees:Obligee:type:SECTION_2'), (3, 'obligees:Obligee:type:SECTION_3'), (4, 'obligees:Obligee:type:SECTION_4')]),
        ),
    ]
