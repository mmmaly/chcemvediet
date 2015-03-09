# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import models, migrations
import multiselectfield.db.fields


class Migration(migrations.Migration):

    dependencies = [
        ('inforequests', '0012_auto_20150304_0050'),
    ]

    operations = [
        migrations.AddField(
            model_name='action',
            name='refusal_reason2',
            field=multiselectfield.db.fields.MultiSelectField(blank=True, help_text='Mandatory multichoice for refusal and affirmation actions, NULL otherwise. Specifies the reason why the obligee refused to disclose the information.', max_length=19, choices=[('3', 'Does not Have Information'), ('4', 'Does not Provide Information'), ('5', 'Does not Create Information'), ('6', 'Copyright Restriction'), ('7', 'Business Secret'), ('8', 'Personal Information'), ('9', 'Confidential Information'), ('-1', 'No Reason Specified'), ('-2', 'Other Reason')]),
            preserve_default=True,
        ),
        migrations.AddField(
            model_name='actiondraft',
            name='refusal_reason2',
            field=multiselectfield.db.fields.MultiSelectField(blank=True, help_text='Optional for refusal and affirmation actions. Must be NULL for all other actions.', max_length=19, choices=[('3', 'Does not Have Information'), ('4', 'Does not Provide Information'), ('5', 'Does not Create Information'), ('6', 'Copyright Restriction'), ('7', 'Business Secret'), ('8', 'Personal Information'), ('9', 'Confidential Information'), ('-1', 'No Reason Specified'), ('-2', 'Other Reason')]),
            preserve_default=True,
        ),
    ]
