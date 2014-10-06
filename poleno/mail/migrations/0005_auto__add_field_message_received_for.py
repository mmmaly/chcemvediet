# -*- coding: utf-8 -*-
from south.utils import datetime_utils as datetime
from south.db import db
from south.v2 import SchemaMigration
from django.db import models


class Migration(SchemaMigration):

    def forwards(self, orm):
        # Adding field 'Message.received_for'
        db.add_column(u'mail_message', 'received_for',
                      self.gf('django.db.models.fields.CharField')(default='', max_length=255, blank=True),
                      keep_default=False)


    def backwards(self, orm):
        # Deleting field 'Message.received_for'
        db.delete_column(u'mail_message', 'received_for')


    models = {
        u'mail.attachment': {
            'Meta': {'ordering': "[u'pk']", 'object_name': 'Attachment'},
            'content_type': ('django.db.models.fields.CharField', [], {'max_length': '255'}),
            'file': ('django.db.models.fields.files.FileField', [], {'max_length': '255'}),
            u'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'message': ('django.db.models.fields.related.ForeignKey', [], {'to': u"orm['mail.Message']"}),
            'name': ('django.db.models.fields.CharField', [], {'max_length': '255'})
        },
        u'mail.message': {
            'Meta': {'ordering': "[u'processed', u'pk']", 'object_name': 'Message'},
            'from_mail': ('django.db.models.fields.CharField', [], {'max_length': '255'}),
            'from_name': ('django.db.models.fields.CharField', [], {'max_length': '255', 'blank': 'True'}),
            'headers': ('jsonfield.fields.JSONField', [], {'default': '{}'}),
            'html': ('django.db.models.fields.TextField', [], {'blank': 'True'}),
            u'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'processed': ('django.db.models.fields.DateTimeField', [], {'null': 'True', 'blank': 'True'}),
            'received_for': ('django.db.models.fields.CharField', [], {'max_length': '255', 'blank': 'True'}),
            'subject': ('django.db.models.fields.CharField', [], {'max_length': '255', 'blank': 'True'}),
            'text': ('django.db.models.fields.TextField', [], {'blank': 'True'}),
            'type': ('django.db.models.fields.SmallIntegerField', [], {})
        },
        u'mail.recipient': {
            'Meta': {'ordering': "[u'pk']", 'object_name': 'Recipient'},
            u'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'mail': ('django.db.models.fields.CharField', [], {'max_length': '255'}),
            'message': ('django.db.models.fields.related.ForeignKey', [], {'to': u"orm['mail.Message']"}),
            'name': ('django.db.models.fields.CharField', [], {'max_length': '255', 'blank': 'True'}),
            'remote_id': ('django.db.models.fields.CharField', [], {'max_length': '255', 'blank': 'True'}),
            'status': ('django.db.models.fields.SmallIntegerField', [], {}),
            'status_details': ('django.db.models.fields.CharField', [], {'max_length': '255', 'blank': 'True'}),
            'type': ('django.db.models.fields.SmallIntegerField', [], {})
        }
    }

    complete_apps = ['mail']