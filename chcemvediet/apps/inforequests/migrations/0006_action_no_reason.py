# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import models, migrations
import multiselectfield.db.fields


class Migration(migrations.Migration):

    dependencies = [
        ('inforequests', '0005_actiondraft_file_number'),
    ]

    operations = [
        migrations.AlterField(
            model_name='action',
            name='refusal_reason',
            field=multiselectfield.db.fields.MultiSelectField(blank=True, help_text='Optional multichoice for refusal and affirmation actions, NULL otherwise. Specifies the reason why the obligee refused to disclose the information. Empty value means that the obligee refused to disclose it with no reason.', max_length=16, choices=[('3', 'Does not Have Information'), ('4', 'Does not Provide Information'), ('5', 'Does not Create Information'), ('6', 'Copyright Restriction'), ('7', 'Business Secret'), ('8', 'Personal Information'), ('9', 'Confidential Information'), ('-2', 'Other Reason')]),
            preserve_default=True,
        ),
        migrations.AlterField(
            model_name='actiondraft',
            name='refusal_reason',
            field=multiselectfield.db.fields.MultiSelectField(blank=True, help_text='Optional multichoice for refusal and affirmation actions. Must be NULL for all other actions.', max_length=16, choices=[('3', 'Does not Have Information'), ('4', 'Does not Provide Information'), ('5', 'Does not Create Information'), ('6', 'Copyright Restriction'), ('7', 'Business Secret'), ('8', 'Personal Information'), ('9', 'Confidential Information'), ('-2', 'Other Reason')]),
            preserve_default=True,
        ),
    ]
