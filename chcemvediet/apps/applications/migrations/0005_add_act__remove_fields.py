# -*- coding: utf-8 -*-
from south.utils import datetime_utils as datetime
from south.db import db
from south.v2 import SchemaMigration
from django.db import models


class Migration(SchemaMigration):

    def forwards(self, orm):
        # Deleting field 'Application.recepient_email'
        db.delete_column(u'applications_application', 'recepient_email')

        # Deleting field 'Application.sender_email'
        db.delete_column(u'applications_application', 'sender_email')

        # Deleting field 'Application.message'
        db.delete_column(u'applications_application', 'message')

        # Deleting field 'Application.subject'
        db.delete_column(u'applications_application', 'subject')

        # Adding unique constraint on 'Application', fields ['unique_email']
        db.create_unique(u'applications_application', ['unique_email'])


    def backwards(self, orm):
        # Removing unique constraint on 'Application', fields ['unique_email']
        db.delete_unique(u'applications_application', ['unique_email'])

        # Adding field 'Application.recepient_email'
        db.add_column(u'applications_application', 'recepient_email',
                      self.gf('django.db.models.fields.EmailField')(default='', max_length=255),
                      keep_default=False)

        # Adding field 'Application.sender_email'
        db.add_column(u'applications_application', 'sender_email',
                      self.gf('django.db.models.fields.EmailField')(default='', max_length=255),
                      keep_default=False)

        # Adding field 'Application.message'
        db.add_column(u'applications_application', 'message',
                      self.gf('django.db.models.fields.TextField')(default=''),
                      keep_default=False)

        # Adding field 'Application.subject'
        db.add_column(u'applications_application', 'subject',
                      self.gf('django.db.models.fields.CharField')(default='', max_length=255),
                      keep_default=False)


    models = {
        u'accounts.profile': {
            'Meta': {'object_name': 'Profile'},
            'city': ('django.db.models.fields.CharField', [], {'max_length': '255'}),
            u'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'street': ('django.db.models.fields.CharField', [], {'max_length': '255'}),
            'user': ('django.db.models.fields.related.OneToOneField', [], {'to': u"orm['auth.User']", 'unique': 'True'}),
            'zip': ('django.db.models.fields.CharField', [], {'max_length': '10'})
        },
        u'applications.act': {
            'Meta': {'object_name': 'Act'},
            'application': ('django.db.models.fields.related.ForeignKey', [], {'to': u"orm['applications.Application']"}),
            'content': ('django.db.models.fields.TextField', [], {}),
            'effective_date': ('django.db.models.fields.DateTimeField', [], {'auto_now_add': 'True', 'blank': 'True'}),
            u'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'subject': ('django.db.models.fields.CharField', [], {'max_length': '255'}),
            'type': ('django.db.models.fields.SmallIntegerField', [], {})
        },
        u'applications.application': {
            'Meta': {'object_name': 'Application'},
            'applicant': ('django.db.models.fields.related.ForeignKey', [], {'to': u"orm['auth.User']"}),
            'applicant_city': ('django.db.models.fields.CharField', [], {'max_length': '255'}),
            'applicant_name': ('django.db.models.fields.CharField', [], {'max_length': '255'}),
            'applicant_street': ('django.db.models.fields.CharField', [], {'max_length': '255'}),
            'applicant_zip': ('django.db.models.fields.CharField', [], {'max_length': '10'}),
            u'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'obligee': ('django.db.models.fields.related.ForeignKey', [], {'to': u"orm['obligees.Obligee']"}),
            'obligee_city': ('django.db.models.fields.CharField', [], {'max_length': '255'}),
            'obligee_name': ('django.db.models.fields.CharField', [], {'max_length': '255'}),
            'obligee_street': ('django.db.models.fields.CharField', [], {'max_length': '255'}),
            'obligee_zip': ('django.db.models.fields.CharField', [], {'max_length': '10'}),
            'submission_date': ('django.db.models.fields.DateTimeField', [], {'auto_now_add': 'True', 'blank': 'True'}),
            'unique_email': ('django.db.models.fields.EmailField', [], {'unique': 'True', 'max_length': '255'})
        },
        u'applications.applicationdraft': {
            'Meta': {'object_name': 'ApplicationDraft'},
            'applicant': ('django.db.models.fields.related.ForeignKey', [], {'to': u"orm['auth.User']"}),
            'content': ('django.db.models.fields.TextField', [], {'blank': 'True'}),
            u'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'obligee': ('django.db.models.fields.related.ForeignKey', [], {'to': u"orm['obligees.Obligee']", 'null': 'True', 'blank': 'True'}),
            'subject': ('django.db.models.fields.CharField', [], {'max_length': '255', 'blank': 'True'})
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

    complete_apps = ['obligees', 'accounts', 'applications']