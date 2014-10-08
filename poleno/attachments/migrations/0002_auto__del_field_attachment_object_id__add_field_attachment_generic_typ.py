# -*- coding: utf-8 -*-
from south.utils import datetime_utils as datetime
from south.db import db
from south.v2 import SchemaMigration
from django.db import models


class Migration(SchemaMigration):

    def forwards(self, orm):
        # Deleting field 'Attachment.object_id'
        db.delete_column(u'attachments_attachment', 'object_id')

        # Adding field 'Attachment.generic_type'
        db.add_column(u'attachments_attachment', 'generic_type',
                      self.gf('django.db.models.fields.related.ForeignKey')(default=0, to=orm['contenttypes.ContentType']),
                      keep_default=False)

        # Adding field 'Attachment.generic_id'
        db.add_column(u'attachments_attachment', 'generic_id',
                      self.gf('django.db.models.fields.PositiveIntegerField')(default=0),
                      keep_default=False)


    def backwards(self, orm):
        # Adding field 'Attachment.object_id'
        db.add_column(u'attachments_attachment', 'object_id',
                      self.gf('django.db.models.fields.PositiveIntegerField')(default=0),
                      keep_default=False)

        # Deleting field 'Attachment.generic_type'
        db.delete_column(u'attachments_attachment', 'generic_type_id')

        # Deleting field 'Attachment.generic_id'
        db.delete_column(u'attachments_attachment', 'generic_id')


    models = {
        u'attachments.attachment': {
            'Meta': {'ordering': "[u'pk']", 'object_name': 'Attachment'},
            'content_type': ('django.db.models.fields.CharField', [], {'max_length': '255'}),
            'created': ('django.db.models.fields.DateTimeField', [], {}),
            'file': ('django.db.models.fields.files.FileField', [], {'max_length': '255'}),
            'generic_id': ('django.db.models.fields.PositiveIntegerField', [], {}),
            'generic_type': ('django.db.models.fields.related.ForeignKey', [], {'to': u"orm['contenttypes.ContentType']"}),
            u'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'name': ('django.db.models.fields.CharField', [], {'max_length': '255'}),
            'size': ('django.db.models.fields.IntegerField', [], {})
        },
        u'contenttypes.contenttype': {
            'Meta': {'ordering': "('name',)", 'unique_together': "(('app_label', 'model'),)", 'object_name': 'ContentType', 'db_table': "'django_content_type'"},
            'app_label': ('django.db.models.fields.CharField', [], {'max_length': '100'}),
            u'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'model': ('django.db.models.fields.CharField', [], {'max_length': '100'}),
            'name': ('django.db.models.fields.CharField', [], {'max_length': '100'})
        }
    }

    complete_apps = ['attachments']