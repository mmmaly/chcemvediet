# -*- coding: utf-8 -*-
from south.utils import datetime_utils as datetime
from south.db import db
from south.v2 import SchemaMigration
from django.db import models


class Migration(SchemaMigration):

    def forwards(self, orm):
        # Adding field 'History.inforequest'
        db.add_column(u'inforequests_history', 'inforequest',
                      self.gf('django.db.models.fields.related.ForeignKey')(related_name=u'history_set', null=True, to=orm['inforequests.Inforequest']),
                      keep_default=False)


        # Changing field 'Inforequest.history'
        db.alter_column(u'inforequests_inforequest', 'history_id', self.gf('django.db.models.fields.related.OneToOneField')(unique=True, null=True, to=orm['inforequests.History']))

    def backwards(self, orm):
        # Deleting field 'History.inforequest'
        db.delete_column(u'inforequests_history', 'inforequest_id')


        # Changing field 'Inforequest.history'
        db.alter_column(u'inforequests_inforequest', 'history_id', self.gf('django.db.models.fields.related.OneToOneField')(default=0, to=orm['inforequests.History'], unique=True))

    models = {
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
            'content': ('django.db.models.fields.TextField', [], {}),
            'deadline': ('django.db.models.fields.IntegerField', [], {'null': 'True', 'blank': 'True'}),
            'disclosure_level': ('django.db.models.fields.SmallIntegerField', [], {'null': 'True', 'blank': 'True'}),
            'effective_date': ('django.db.models.fields.DateTimeField', [], {}),
            'history': ('django.db.models.fields.related.ForeignKey', [], {'to': u"orm['inforequests.History']"}),
            u'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'receivedemail': ('django.db.models.fields.related.OneToOneField', [], {'to': u"orm['inforequests.ReceivedEmail']", 'unique': 'True', 'null': 'True', 'blank': 'True'}),
            'refusal_reason': ('django.db.models.fields.SmallIntegerField', [], {'null': 'True', 'blank': 'True'}),
            'subject': ('django.db.models.fields.CharField', [], {'max_length': '255'}),
            'type': ('django.db.models.fields.SmallIntegerField', [], {})
        },
        u'inforequests.history': {
            'Meta': {'object_name': 'History'},
            'advanced_by': ('django.db.models.fields.related.ForeignKey', [], {'blank': 'True', 'related_name': "u'advanced_to_set'", 'null': 'True', 'to': u"orm['inforequests.Action']"}),
            u'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'inforequest': ('django.db.models.fields.related.ForeignKey', [], {'related_name': "u'history_set'", 'null': 'True', 'to': u"orm['inforequests.Inforequest']"}),
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
            'history': ('django.db.models.fields.related.OneToOneField', [], {'related_name': "u'inforequest_'", 'unique': 'True', 'null': 'True', 'to': u"orm['inforequests.History']"}),
            u'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'submission_date': ('django.db.models.fields.DateTimeField', [], {'auto_now_add': 'True', 'blank': 'True'}),
            'unique_email': ('django.db.models.fields.EmailField', [], {'unique': 'True', 'max_length': '255'})
        },
        u'inforequests.inforequestdraft': {
            'Meta': {'ordering': "[u'pk']", 'object_name': 'InforequestDraft'},
            'applicant': ('django.db.models.fields.related.ForeignKey', [], {'to': u"orm['auth.User']"}),
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