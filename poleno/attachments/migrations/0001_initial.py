# -*- coding: utf-8 -*-
from south.utils import datetime_utils as datetime
from south.db import db
from south.v2 import SchemaMigration
from django.db import models


class Migration(SchemaMigration):

    def forwards(self, orm):
        # Adding model 'Attachment'
        db.create_table(u'attachments_attachment', (
            (u'id', self.gf('django.db.models.fields.AutoField')(primary_key=True)),
            ('object_id', self.gf('django.db.models.fields.PositiveIntegerField')()),
            ('file', self.gf('django.db.models.fields.files.FileField')(max_length=255)),
            ('name', self.gf('django.db.models.fields.CharField')(max_length=255)),
            ('content_type', self.gf('django.db.models.fields.CharField')(max_length=255)),
            ('created', self.gf('django.db.models.fields.DateTimeField')()),
            ('size', self.gf('django.db.models.fields.IntegerField')()),
        ))
        db.send_create_signal(u'attachments', ['Attachment'])


    def backwards(self, orm):
        # Deleting model 'Attachment'
        db.delete_table(u'attachments_attachment')


    models = {
        u'attachments.attachment': {
            'Meta': {'ordering': "[u'pk']", 'object_name': 'Attachment'},
            'content_type': ('django.db.models.fields.CharField', [], {'max_length': '255'}),
            'created': ('django.db.models.fields.DateTimeField', [], {}),
            'file': ('django.db.models.fields.files.FileField', [], {'max_length': '255'}),
            u'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'name': ('django.db.models.fields.CharField', [], {'max_length': '255'}),
            'object_id': ('django.db.models.fields.PositiveIntegerField', [], {}),
            'size': ('django.db.models.fields.IntegerField', [], {})
        }
    }

    complete_apps = ['attachments']