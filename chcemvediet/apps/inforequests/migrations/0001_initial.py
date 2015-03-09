# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import models, migrations
import jsonfield.fields
import django.db.models.deletion
import multiselectfield.db.fields
from django.conf import settings


class Migration(migrations.Migration):

    dependencies = [
        migrations.swappable_dependency(settings.AUTH_USER_MODEL),
        ('obligees', '0001_initial'),
        ('mail', '0001_initial'),
    ]

    operations = [
        migrations.CreateModel(
            name='Action',
            fields=[
                ('id', models.AutoField(verbose_name='ID', serialize=False, auto_created=True, primary_key=True)),
                ('type', models.SmallIntegerField(choices=[(1, 'Request'), (12, 'Clarification Response'), (13, 'Appeal'), (2, 'Confirmation'), (3, 'Extension'), (4, 'Advancement'), (5, 'Clarification Request'), (6, 'Disclosure'), (7, 'Refusal'), (8, 'Affirmation'), (9, 'Reversion'), (10, 'Remandment'), (11, 'Advanced Request'), (14, 'Expiration'), (15, 'Appeal Expiration')])),
                ('subject', models.CharField(max_length=255, blank=True)),
                ('content', models.TextField(blank=True)),
                ('effective_date', models.DateField(help_text="The date at which the action was sent or received. If the action was sent/received by e\u2011mail it's set automatically. If it was sent/received by s\u2011mail it's filled by the applicant.")),
                ('deadline', models.IntegerField(help_text='The deadline that apply after the action, if the action sets a deadline, NULL otherwise. The deadline is expressed in a number of working days (WD) counting since the effective date. It may apply to the applicant or to the obligee, depending on the action type.', null=True, blank=True)),
                ('extension', models.IntegerField(help_text='Applicant extension to the deadline, if the action sets an obligee deadline. The applicant may extend the deadline after it is missed in order to be patient and wait a little longer. He may extend it multiple times. Applicant deadlines may not be extended.', null=True, blank=True)),
                ('disclosure_level', models.SmallIntegerField(blank=True, help_text='Mandatory choice for advancement, disclosure, reversion and remandment actions, NULL otherwise. Specifies if the obligee disclosed any requested information by this action.', null=True, choices=[(1, 'No Disclosure at All'), (2, 'Partial Disclosure'), (3, 'Full Disclosure')])),
                ('refusal_reason', multiselectfield.db.fields.MultiSelectField(blank=True, help_text='Mandatory multichoice for refusal and affirmation actions, NULL otherwise. Specifies the reason why the obligee refused to disclose the information.', max_length=19, choices=[('3', 'Does not Have Information'), ('4', 'Does not Provide Information'), ('5', 'Does not Create Information'), ('6', 'Copyright Restriction'), ('7', 'Business Secret'), ('8', 'Personal Information'), ('9', 'Confidential Information'), ('-1', 'No Reason Specified'), ('-2', 'Other Reason')])),
                ('last_deadline_reminder', models.DateTimeField(null=True, blank=True)),
            ],
            options={
            },
            bases=(models.Model,),
        ),
        migrations.CreateModel(
            name='ActionDraft',
            fields=[
                ('id', models.AutoField(verbose_name='ID', serialize=False, auto_created=True, primary_key=True)),
                ('type', models.SmallIntegerField(choices=[(1, 'Request'), (12, 'Clarification Response'), (13, 'Appeal'), (2, 'Confirmation'), (3, 'Extension'), (4, 'Advancement'), (5, 'Clarification Request'), (6, 'Disclosure'), (7, 'Refusal'), (8, 'Affirmation'), (9, 'Reversion'), (10, 'Remandment'), (11, 'Advanced Request'), (14, 'Expiration'), (15, 'Appeal Expiration')])),
                ('subject', models.CharField(max_length=255, blank=True)),
                ('content', models.TextField(blank=True)),
                ('effective_date', models.DateField(null=True, blank=True)),
                ('deadline', models.IntegerField(help_text='Optional for extension actions. Must be NULL for all other actions.', null=True, blank=True)),
                ('disclosure_level', models.SmallIntegerField(blank=True, help_text='Optional for advancement, disclosure, reversion and remandment actions. Must be NULL for all other actions.', null=True, choices=[(1, 'No Disclosure at All'), (2, 'Partial Disclosure'), (3, 'Full Disclosure')])),
                ('refusal_reason', multiselectfield.db.fields.MultiSelectField(blank=True, help_text='Optional for refusal and affirmation actions. Must be NULL for all other actions.', max_length=19, choices=[('3', 'Does not Have Information'), ('4', 'Does not Provide Information'), ('5', 'Does not Create Information'), ('6', 'Copyright Restriction'), ('7', 'Business Secret'), ('8', 'Personal Information'), ('9', 'Confidential Information'), ('-1', 'No Reason Specified'), ('-2', 'Other Reason')])),
            ],
            options={
            },
            bases=(models.Model,),
        ),
        migrations.CreateModel(
            name='Branch',
            fields=[
                ('id', models.AutoField(verbose_name='ID', serialize=False, auto_created=True, primary_key=True)),
                ('advanced_by', models.ForeignKey(related_name='advanced_to_set', blank=True, to='inforequests.Action', help_text='NULL for main branches. The advancement action the inforequest was advanced by for advanced branches. Every Inforequest must contain exactly one main branch.', null=True, db_index=False)),
                ('historicalobligee', models.ForeignKey(help_text='Frozen Obligee at the time the Inforequest was submitted or advanced to it.', to='obligees.HistoricalObligee')),
            ],
            options={
                'verbose_name_plural': 'Branches',
            },
            bases=(models.Model,),
        ),
        migrations.CreateModel(
            name='Inforequest',
            fields=[
                ('id', models.AutoField(verbose_name='ID', serialize=False, auto_created=True, primary_key=True)),
                ('applicant_name', models.CharField(help_text='Frozen applicant contact information for the case he changes it in the future. The information is frozen to its state at the moment the inforequest was submitted.', max_length=255)),
                ('applicant_street', models.CharField(max_length=255)),
                ('applicant_city', models.CharField(max_length=255)),
                ('applicant_zip', models.CharField(max_length=10)),
                ('unique_email', models.EmailField(help_text='Unique email address used to identify which obligee email belongs to which inforequest. If the inforequest was advanced to other obligees, the same email address is used for communication with all such obligees, as there is no way to tell them to send their response to a different email address.', unique=True, max_length=255, db_index=True)),
                ('submission_date', models.DateField(auto_now_add=True)),
                ('closed', models.BooleanField(default=False, help_text='True if the inforequest is closed and the applicant may not act on it any more.')),
                ('last_undecided_email_reminder', models.DateTimeField(null=True, blank=True)),
                ('applicant', models.ForeignKey(help_text='The inforequest owner, the user who submitted it.', to=settings.AUTH_USER_MODEL)),
            ],
            options={
            },
            bases=(models.Model,),
        ),
        migrations.CreateModel(
            name='InforequestDraft',
            fields=[
                ('id', models.AutoField(verbose_name='ID', serialize=False, auto_created=True, primary_key=True)),
                ('subject', jsonfield.fields.JSONField(default=(), blank=True)),
                ('content', jsonfield.fields.JSONField(default=(), blank=True)),
                ('applicant', models.ForeignKey(help_text='The draft owner, the future inforequest applicant.', to=settings.AUTH_USER_MODEL)),
                ('obligee', models.ForeignKey(blank=True, to='obligees.Obligee', help_text='The obligee the inforequest will be sent to, if the user has already set it.', null=True)),
            ],
            options={
            },
            bases=(models.Model,),
        ),
        migrations.CreateModel(
            name='InforequestEmail',
            fields=[
                ('id', models.AutoField(verbose_name='ID', serialize=False, auto_created=True, primary_key=True)),
                ('type', models.SmallIntegerField(help_text='"Applicant Action": the email represents an applicant action; "Obligee Action": the email represents an obligee action; "Undecided": The email is waiting for applicant decision; "Unrelated": Marked as an unrelated email; "Unknown": Marked as an email the applicant didn\'t know how to decide. It must be "Applicant Action" for outbound mesages or one of the remaining values for inbound messages.', choices=[(1, 'Applicant Action'), (2, 'Obligee Action'), (3, 'Undecided'), (4, 'Unrelated'), (5, 'Unknown')])),
                ('email', models.ForeignKey(to='mail.Message', db_index=False)),
                ('inforequest', models.ForeignKey(to='inforequests.Inforequest', db_index=False)),
            ],
            options={
            },
            bases=(models.Model,),
        ),
        migrations.AlterIndexTogether(
            name='inforequestemail',
            index_together=set([('inforequest', 'email'), ('email', 'inforequest'), ('type', 'inforequest')]),
        ),
        migrations.AddField(
            model_name='inforequest',
            name='email_set',
            field=models.ManyToManyField(to='mail.Message', through='inforequests.InforequestEmail'),
            preserve_default=True,
        ),
        migrations.AlterIndexTogether(
            name='inforequest',
            index_together=set([('submission_date', 'id')]),
        ),
        migrations.AddField(
            model_name='branch',
            name='inforequest',
            field=models.ForeignKey(to='inforequests.Inforequest', db_index=False),
            preserve_default=True,
        ),
        migrations.AddField(
            model_name='branch',
            name='obligee',
            field=models.ForeignKey(help_text='The obligee the inforequest was sent or advanced to.', to='obligees.Obligee'),
            preserve_default=True,
        ),
        migrations.AlterIndexTogether(
            name='branch',
            index_together=set([('inforequest', 'advanced_by'), ('advanced_by', 'inforequest')]),
        ),
        migrations.AddField(
            model_name='actiondraft',
            name='branch',
            field=models.ForeignKey(blank=True, to='inforequests.Branch', help_text='Must be owned by inforequest if set', null=True),
            preserve_default=True,
        ),
        migrations.AddField(
            model_name='actiondraft',
            name='inforequest',
            field=models.ForeignKey(to='inforequests.Inforequest'),
            preserve_default=True,
        ),
        migrations.AddField(
            model_name='actiondraft',
            name='obligee_set',
            field=models.ManyToManyField(help_text='May be empty for advancement actions. Must be empty for all other actions.', to='obligees.Obligee', blank=True),
            preserve_default=True,
        ),
        migrations.AddField(
            model_name='action',
            name='branch',
            field=models.ForeignKey(to='inforequests.Branch'),
            preserve_default=True,
        ),
        migrations.AddField(
            model_name='action',
            name='email',
            field=models.OneToOneField(null=True, on_delete=django.db.models.deletion.SET_NULL, blank=True, to='mail.Message'),
            preserve_default=True,
        ),
        migrations.AlterIndexTogether(
            name='action',
            index_together=set([('effective_date', 'id')]),
        ),
    ]
