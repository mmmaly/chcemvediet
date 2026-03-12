# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import migrations, models
import multiselectfield.db.fields


class Migration(migrations.Migration):

    dependencies = [
        ('inforequests', '0025_auto_20231226_2247'),
    ]

    operations = [
        migrations.AlterField(
            model_name='action',
            name='disclosure_level',
            field=models.SmallIntegerField(blank=True, help_text='Mandatory choice for obligee actions that may disclose the information, NULL otherwise. Specifies if the obligee disclosed any requested information by this action.', null=True, choices=[(1, 'inforequests:Action:disclosure_level:NONE'), (2, 'inforequests:Action:disclosure_level:PARTIAL'), (3, 'inforequests:Action:disclosure_level:FULL')]),
        ),
        migrations.AlterField(
            model_name='action',
            name='refusal_reason',
            field=multiselectfield.db.fields.MultiSelectField(blank=True, help_text='Optional multichoice for obligee actions that may provide a reason for not disclosing the information, Should be empty for all other actions. Specifies the reason why the obligee refused to disclose the information. An empty value means that the obligee did not provide any reason.', max_length=16, choices=[('3', 'inforequests:Action:refusal_reason:DOES_NOT_HAVE'), ('4', 'inforequests:Action:refusal_reason:DOES_NOT_PROVIDE'), ('5', 'inforequests:Action:refusal_reason:DOES_NOT_CREATE'), ('6', 'inforequests:Action:refusal_reason:COPYRIGHT'), ('7', 'inforequests:Action:refusal_reason:BUSINESS_SECRET'), ('8', 'inforequests:Action:refusal_reason:PERSONAL'), ('9', 'inforequests:Action:refusal_reason:CONFIDENTIAL'), ('-2', 'inforequests:Action:refusal_reason:OTHER_REASON')]),
        ),
        migrations.AlterField(
            model_name='action',
            name='type',
            field=models.SmallIntegerField(choices=[(1, 'inforequests:Action:type:REQUEST'), (12, 'inforequests:Action:type:CLARIFICATION_RESPONSE'), (13, 'inforequests:Action:type:APPEAL'), (2, 'inforequests:Action:type:CONFIRMATION'), (3, 'inforequests:Action:type:EXTENSION'), (4, 'inforequests:Action:type:ADVANCEMENT'), (5, 'inforequests:Action:type:CLARIFICATION_REQUEST'), (6, 'inforequests:Action:type:DISCLOSURE'), (7, 'inforequests:Action:type:REFUSAL'), (8, 'inforequests:Action:type:AFFIRMATION'), (9, 'inforequests:Action:type:REVERSION'), (10, 'inforequests:Action:type:REMANDMENT'), (11, 'inforequests:Action:type:ADVANCED_REQUEST'), (14, 'inforequests:Action:type:EXPIRATION'), (15, 'inforequests:Action:type:APPEAL_EXPIRATION')]),
        ),
        migrations.AlterField(
            model_name='feedback',
            name='rating',
            field=models.SmallIntegerField(default=None, null=True, blank=True, choices=[(0, 'inforequests:Feedback:rating:ATROCIOUS'), (1, 'inforequests:Feedback:rating:VERY_POOR'), (2, 'inforequests:Feedback:rating:POOR'), (3, 'inforequests:Feedback:rating:MEDIOCRE'), (4, 'inforequests:Feedback:rating:GOOD'), (5, 'inforequests:Feedback:rating:VERY_GOOD'), (6, 'inforequests:Feedback:rating:EXCELLENT')]),
        ),
        migrations.AlterField(
            model_name='inforequestemail',
            name='type',
            field=models.SmallIntegerField(help_text='"Applicant Action": the email represents an applicant action; "Obligee Action": the email represents an obligee action; "Undecided": The email is waiting for applicant decision; "Unrelated": Marked as an unrelated email; "Unknown": Marked as an email the applicant didn\'t know how to decide. It must be "Applicant Action" for outbound mesages or one of the remaining values for inbound messages.', choices=[(1, 'inforequests:InforequestEmail:type:APPLICANT_ACTION'), (2, 'inforequests:InforequestEmail:type:OBLIGEE_ACTION'), (3, 'inforequests:InforequestEmail:type:UNDECIDED'), (4, 'inforequests:InforequestEmail:type:UNRELATED'), (5, 'inforequests:InforequestEmail:type:UNKNOWN')]),
        ),
    ]
