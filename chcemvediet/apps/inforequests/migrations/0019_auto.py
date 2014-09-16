# -*- coding: utf-8 -*-
from south.utils import datetime_utils as datetime
from south.db import db
from south.v2 import SchemaMigration
from django.db import models


class Migration(SchemaMigration):

    def forwards(self, orm):
        # Adding M2M table for field attachment_set on 'Action'
        m2m_table_name = db.shorten_name(u'inforequests_action_attachment_set')
        db.create_table(m2m_table_name, (
            ('id', models.AutoField(verbose_name='ID', primary_key=True, auto_created=True)),
            ('action', models.ForeignKey(orm[u'inforequests.action'], null=False)),
            ('attachment', models.ForeignKey(orm[u'attachments.attachment'], null=False))
        ))
        db.create_unique(m2m_table_name, ['action_id', 'attachment_id'])

        # Adding M2M table for field attachment_set on 'ActionDraft'
        m2m_table_name = db.shorten_name(u'inforequests_actiondraft_attachment_set')
        db.create_table(m2m_table_name, (
            ('id', models.AutoField(verbose_name='ID', primary_key=True, auto_created=True)),
            ('actiondraft', models.ForeignKey(orm[u'inforequests.actiondraft'], null=False)),
            ('attachment', models.ForeignKey(orm[u'attachments.attachment'], null=False))
        ))
        db.create_unique(m2m_table_name, ['actiondraft_id', 'attachment_id'])

        # Adding M2M table for field attachment_set on 'InforequestDraft'
        m2m_table_name = db.shorten_name(u'inforequests_inforequestdraft_attachment_set')
        db.create_table(m2m_table_name, (
            ('id', models.AutoField(verbose_name='ID', primary_key=True, auto_created=True)),
            ('inforequestdraft', models.ForeignKey(orm[u'inforequests.inforequestdraft'], null=False)),
            ('attachment', models.ForeignKey(orm[u'attachments.attachment'], null=False))
        ))
        db.create_unique(m2m_table_name, ['inforequestdraft_id', 'attachment_id'])


    def backwards(self, orm):
        # Removing M2M table for field attachment_set on 'Action'
        db.delete_table(db.shorten_name(u'inforequests_action_attachment_set'))

        # Removing M2M table for field attachment_set on 'ActionDraft'
        db.delete_table(db.shorten_name(u'inforequests_actiondraft_attachment_set'))

        # Removing M2M table for field attachment_set on 'InforequestDraft'
        db.delete_table(db.shorten_name(u'inforequests_inforequestdraft_attachment_set'))


    models = {
        u'attachments.attachment': {
            'Meta': {'ordering': "[u'pk']", 'object_name': 'Attachment'},
            'content_type': ('django.db.models.fields.CharField', [], {'max_length': '255'}),
            'file': ('django.db.models.fields.files.FileField', [], {'max_length': '255'}),
            u'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'name': ('django.db.models.fields.CharField', [], {'max_length': '255'}),
            'owner': ('django.db.models.fields.related.ForeignKey', [], {'to': u"orm['auth.User']"}),
            'size': ('django.db.models.fields.IntegerField', [], {})
        },
        u'auth.group': {
            'Meta': {'object_name': 'Group'},
            u'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'name': ('django.db.models.fields.CharField', [], {'unique': 'True', 'max_length': '80'}),
            'permissions': ('django.db.models.fields.related.ManyToManyField', [], {'to': u"orm['auth.Permission']", 'symmetrical': 'False', 'blank': 'True'})
        },
        u'auth.permission': {
            'Meta': {'ordering': "(u'content_type__app_label', u'content_type__model', u'codename')", 'unique_together': "((u'content_type', u'codename'),)", 'object_name': 'Permission'},
            'codename': ('django.db.models.fields.CharField', [], {'max_length': '100'}),
            'content_type': ('django.db.models.fields.related.ForeignKey', [], {'to': u"orm['contenttypes.ContentType']"}),
            u'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'name': ('django.db.models.fields.CharField', [], {'max_length': '50'})
        },
        u'auth.user': {
            'Meta': {'object_name': 'User'},
            'date_joined': ('django.db.models.fields.DateTimeField', [], {'default': 'datetime.datetime.now'}),
            'email': ('django.db.models.fields.EmailField', [], {'max_length': '75', 'blank': 'True'}),
            'first_name': ('django.db.models.fields.CharField', [], {'max_length': '30', 'blank': 'True'}),
            'groups': ('django.db.models.fields.related.ManyToManyField', [], {'symmetrical': 'False', 'related_name': "u'user_set'", 'blank': 'True', 'to': u"orm['auth.Group']"}),
            u'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'is_active': ('django.db.models.fields.BooleanField', [], {'default': 'True'}),
            'is_staff': ('django.db.models.fields.BooleanField', [], {'default': 'False'}),
            'is_superuser': ('django.db.models.fields.BooleanField', [], {'default': 'False'}),
            'last_login': ('django.db.models.fields.DateTimeField', [], {'default': 'datetime.datetime.now'}),
            'last_name': ('django.db.models.fields.CharField', [], {'max_length': '30', 'blank': 'True'}),
            'password': ('django.db.models.fields.CharField', [], {'max_length': '128'}),
            'user_permissions': ('django.db.models.fields.related.ManyToManyField', [], {'symmetrical': 'False', 'related_name': "u'user_set'", 'blank': 'True', 'to': u"orm['auth.Permission']"}),
            'username': ('django.db.models.fields.CharField', [], {'unique': 'True', 'max_length': '30'})
        },
        u'contenttypes.contenttype': {
            'Meta': {'ordering': "('name',)", 'unique_together': "(('app_label', 'model'),)", 'object_name': 'ContentType', 'db_table': "'django_content_type'"},
            'app_label': ('django.db.models.fields.CharField', [], {'max_length': '100'}),
            u'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'model': ('django.db.models.fields.CharField', [], {'max_length': '100'}),
            'name': ('django.db.models.fields.CharField', [], {'max_length': '100'})
        },
        u'django_mailbox.mailbox': {
            'Meta': {'object_name': 'Mailbox'},
            'active': ('django.db.models.fields.BooleanField', [], {'default': 'True'}),
            'from_email': ('django.db.models.fields.CharField', [], {'default': 'None', 'max_length': '255', 'null': 'True', 'blank': 'True'}),
            u'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'name': ('django.db.models.fields.CharField', [], {'max_length': '255'}),
            'uri': ('django.db.models.fields.CharField', [], {'default': 'None', 'max_length': '255', 'null': 'True', 'blank': 'True'})
        },
        u'django_mailbox.message': {
            'Meta': {'object_name': 'Message'},
            'body': ('django.db.models.fields.TextField', [], {}),
            'encoded': ('django.db.models.fields.BooleanField', [], {'default': 'False'}),
            'from_header': ('django.db.models.fields.CharField', [], {'max_length': '255'}),
            u'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'in_reply_to': ('django.db.models.fields.related.ForeignKey', [], {'blank': 'True', 'related_name': "'replies'", 'null': 'True', 'to': u"orm['django_mailbox.Message']"}),
            'mailbox': ('django.db.models.fields.related.ForeignKey', [], {'related_name': "'messages'", 'to': u"orm['django_mailbox.Mailbox']"}),
            'message_id': ('django.db.models.fields.CharField', [], {'max_length': '255'}),
            'outgoing': ('django.db.models.fields.BooleanField', [], {'default': 'False'}),
            'processed': ('django.db.models.fields.DateTimeField', [], {'auto_now_add': 'True', 'blank': 'True'}),
            'read': ('django.db.models.fields.DateTimeField', [], {'default': 'None', 'null': 'True', 'blank': 'True'}),
            'subject': ('django.db.models.fields.CharField', [], {'max_length': '255'}),
            'to_header': ('django.db.models.fields.TextField', [], {})
        },
        u'inforequests.action': {
            'Meta': {'ordering': "[u'effective_date', u'pk']", 'object_name': 'Action'},
            'attachment_set': ('django.db.models.fields.related.ManyToManyField', [], {'to': u"orm['attachments.Attachment']", 'symmetrical': 'False'}),
            'content': ('django.db.models.fields.TextField', [], {'blank': 'True'}),
            'deadline': ('django.db.models.fields.IntegerField', [], {'null': 'True', 'blank': 'True'}),
            'disclosure_level': ('django.db.models.fields.SmallIntegerField', [], {'null': 'True', 'blank': 'True'}),
            'effective_date': ('django.db.models.fields.DateField', [], {}),
            'extension': ('django.db.models.fields.IntegerField', [], {'null': 'True', 'blank': 'True'}),
            'history': ('django.db.models.fields.related.ForeignKey', [], {'to': u"orm['inforequests.History']"}),
            u'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'receivedemail': ('django.db.models.fields.related.OneToOneField', [], {'to': u"orm['inforequests.ReceivedEmail']", 'unique': 'True', 'null': 'True', 'blank': 'True'}),
            'refusal_reason': ('django.db.models.fields.SmallIntegerField', [], {'null': 'True', 'blank': 'True'}),
            'subject': ('django.db.models.fields.CharField', [], {'max_length': '255', 'blank': 'True'}),
            'type': ('django.db.models.fields.SmallIntegerField', [], {})
        },
        u'inforequests.actiondraft': {
            'Meta': {'ordering': "[u'pk']", 'object_name': 'ActionDraft'},
            'attachment_set': ('django.db.models.fields.related.ManyToManyField', [], {'to': u"orm['attachments.Attachment']", 'symmetrical': 'False'}),
            'content': ('django.db.models.fields.TextField', [], {'blank': 'True'}),
            'deadline': ('django.db.models.fields.IntegerField', [], {'null': 'True', 'blank': 'True'}),
            'disclosure_level': ('django.db.models.fields.SmallIntegerField', [], {'null': 'True', 'blank': 'True'}),
            'effective_date': ('django.db.models.fields.DateField', [], {'null': 'True', 'blank': 'True'}),
            'history': ('django.db.models.fields.related.ForeignKey', [], {'to': u"orm['inforequests.History']", 'null': 'True', 'blank': 'True'}),
            u'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'inforequest': ('django.db.models.fields.related.ForeignKey', [], {'to': u"orm['inforequests.Inforequest']"}),
            'obligee_set': ('django.db.models.fields.related.ManyToManyField', [], {'to': u"orm['obligees.Obligee']", 'symmetrical': 'False'}),
            'refusal_reason': ('django.db.models.fields.SmallIntegerField', [], {'null': 'True', 'blank': 'True'}),
            'subject': ('django.db.models.fields.CharField', [], {'max_length': '255', 'blank': 'True'}),
            'type': ('django.db.models.fields.SmallIntegerField', [], {})
        },
        u'inforequests.history': {
            'Meta': {'ordering': "[u'obligee_name', u'pk']", 'object_name': 'History'},
            'advanced_by': ('django.db.models.fields.related.ForeignKey', [], {'blank': 'True', 'related_name': "u'advanced_to_set'", 'null': 'True', 'to': u"orm['inforequests.Action']"}),
            u'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'inforequest': ('django.db.models.fields.related.ForeignKey', [], {'to': u"orm['inforequests.Inforequest']"}),
            'obligee': ('django.db.models.fields.related.ForeignKey', [], {'to': u"orm['obligees.Obligee']"}),
            'obligee_city': ('django.db.models.fields.CharField', [], {'max_length': '255'}),
            'obligee_name': ('django.db.models.fields.CharField', [], {'max_length': '255'}),
            'obligee_street': ('django.db.models.fields.CharField', [], {'max_length': '255'}),
            'obligee_zip': ('django.db.models.fields.CharField', [], {'max_length': '10'})
        },
        u'inforequests.inforequest': {
            'Meta': {'ordering': "[u'submission_date', u'pk']", 'object_name': 'Inforequest'},
            'applicant': ('django.db.models.fields.related.ForeignKey', [], {'to': u"orm['auth.User']"}),
            'applicant_city': ('django.db.models.fields.CharField', [], {'max_length': '255'}),
            'applicant_name': ('django.db.models.fields.CharField', [], {'max_length': '255'}),
            'applicant_street': ('django.db.models.fields.CharField', [], {'max_length': '255'}),
            'applicant_zip': ('django.db.models.fields.CharField', [], {'max_length': '10'}),
            u'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'submission_date': ('django.db.models.fields.DateField', [], {'auto_now_add': 'True', 'blank': 'True'}),
            'unique_email': ('django.db.models.fields.EmailField', [], {'unique': 'True', 'max_length': '255'})
        },
        u'inforequests.inforequestdraft': {
            'Meta': {'ordering': "[u'pk']", 'object_name': 'InforequestDraft'},
            'applicant': ('django.db.models.fields.related.ForeignKey', [], {'to': u"orm['auth.User']"}),
            'attachment_set': ('django.db.models.fields.related.ManyToManyField', [], {'to': u"orm['attachments.Attachment']", 'symmetrical': 'False'}),
            'content': ('django.db.models.fields.TextField', [], {'blank': 'True'}),
            u'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'obligee': ('django.db.models.fields.related.ForeignKey', [], {'to': u"orm['obligees.Obligee']", 'null': 'True', 'blank': 'True'}),
            'subject': ('django.db.models.fields.CharField', [], {'max_length': '255', 'blank': 'True'})
        },
        u'inforequests.receivedemail': {
            'Meta': {'ordering': "[u'raw_email__processed', u'pk']", 'object_name': 'ReceivedEmail'},
            u'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'inforequest': ('django.db.models.fields.related.ForeignKey', [], {'to': u"orm['inforequests.Inforequest']", 'null': 'True', 'blank': 'True'}),
            'raw_email': ('django.db.models.fields.related.ForeignKey', [], {'to': u"orm['django_mailbox.Message']"}),
            'status': ('django.db.models.fields.SmallIntegerField', [], {})
        },
        u'obligees.obligee': {
            'Meta': {'object_name': 'Obligee'},
            'city': ('django.db.models.fields.CharField', [], {'max_length': '255'}),
            'email': ('django.db.models.fields.EmailField', [], {'max_length': '255'}),
            u'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'name': ('django.db.models.fields.CharField', [], {'max_length': '255'}),
            'slug': ('django.db.models.fields.SlugField', [], {'max_length': '255'}),
            'street': ('django.db.models.fields.CharField', [], {'max_length': '255'}),
            'zip': ('django.db.models.fields.CharField', [], {'max_length': '10'})
        }
    }

    complete_apps = ['inforequests']