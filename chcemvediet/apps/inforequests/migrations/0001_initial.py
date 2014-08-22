# -*- coding: utf-8 -*-
from south.utils import datetime_utils as datetime
from south.db import db
from south.v2 import SchemaMigration
from django.db import models


class Migration(SchemaMigration):

    def forwards(self, orm):
        # Adding model 'InforequestDraft'
        db.create_table(u'inforequests_inforequestdraft', (
            (u'id', self.gf('django.db.models.fields.AutoField')(primary_key=True)),
            ('applicant', self.gf('django.db.models.fields.related.ForeignKey')(to=orm['auth.User'])),
            ('obligee', self.gf('django.db.models.fields.related.ForeignKey')(to=orm['obligees.Obligee'], null=True, blank=True)),
            ('subject', self.gf('django.db.models.fields.CharField')(max_length=255, blank=True)),
            ('content', self.gf('django.db.models.fields.TextField')(blank=True)),
        ))
        db.send_create_signal(u'inforequests', ['InforequestDraft'])

        # Adding model 'Inforequest'
        db.create_table(u'inforequests_inforequest', (
            (u'id', self.gf('django.db.models.fields.AutoField')(primary_key=True)),
            ('applicant', self.gf('django.db.models.fields.related.ForeignKey')(to=orm['auth.User'])),
            ('history', self.gf('django.db.models.fields.related.OneToOneField')(to=orm['inforequests.History'], unique=True)),
            ('unique_email', self.gf('django.db.models.fields.EmailField')(unique=True, max_length=255)),
            ('submission_date', self.gf('django.db.models.fields.DateTimeField')(auto_now_add=True, blank=True)),
            ('applicant_name', self.gf('django.db.models.fields.CharField')(max_length=255)),
            ('applicant_street', self.gf('django.db.models.fields.CharField')(max_length=255)),
            ('applicant_city', self.gf('django.db.models.fields.CharField')(max_length=255)),
            ('applicant_zip', self.gf('django.db.models.fields.CharField')(max_length=10)),
        ))
        db.send_create_signal(u'inforequests', ['Inforequest'])

        # Adding model 'History'
        db.create_table(u'inforequests_history', (
            (u'id', self.gf('django.db.models.fields.AutoField')(primary_key=True)),
            ('obligee', self.gf('django.db.models.fields.related.ForeignKey')(to=orm['obligees.Obligee'])),
            ('obligee_name', self.gf('django.db.models.fields.CharField')(max_length=255)),
            ('obligee_street', self.gf('django.db.models.fields.CharField')(max_length=255)),
            ('obligee_city', self.gf('django.db.models.fields.CharField')(max_length=255)),
            ('obligee_zip', self.gf('django.db.models.fields.CharField')(max_length=10)),
        ))
        db.send_create_signal(u'inforequests', ['History'])

        # Adding model 'Action'
        db.create_table(u'inforequests_action', (
            (u'id', self.gf('django.db.models.fields.AutoField')(primary_key=True)),
            ('type', self.gf('django.db.models.fields.SmallIntegerField')()),
            ('history', self.gf('django.db.models.fields.related.ForeignKey')(to=orm['inforequests.History'])),
            ('subject', self.gf('django.db.models.fields.CharField')(max_length=255)),
            ('content', self.gf('django.db.models.fields.TextField')()),
            ('effective_date', self.gf('django.db.models.fields.DateTimeField')(auto_now_add=True, blank=True)),
        ))
        db.send_create_signal(u'inforequests', ['Action'])


    def backwards(self, orm):
        # Deleting model 'InforequestDraft'
        db.delete_table(u'inforequests_inforequestdraft')

        # Deleting model 'Inforequest'
        db.delete_table(u'inforequests_inforequest')

        # Deleting model 'History'
        db.delete_table(u'inforequests_history')

        # Deleting model 'Action'
        db.delete_table(u'inforequests_action')


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
        u'inforequests.action': {
            'Meta': {'object_name': 'Action'},
            'content': ('django.db.models.fields.TextField', [], {}),
            'effective_date': ('django.db.models.fields.DateTimeField', [], {'auto_now_add': 'True', 'blank': 'True'}),
            'history': ('django.db.models.fields.related.ForeignKey', [], {'to': u"orm['inforequests.History']"}),
            u'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'subject': ('django.db.models.fields.CharField', [], {'max_length': '255'}),
            'type': ('django.db.models.fields.SmallIntegerField', [], {})
        },
        u'inforequests.history': {
            'Meta': {'object_name': 'History'},
            u'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'obligee': ('django.db.models.fields.related.ForeignKey', [], {'to': u"orm['obligees.Obligee']"}),
            'obligee_city': ('django.db.models.fields.CharField', [], {'max_length': '255'}),
            'obligee_name': ('django.db.models.fields.CharField', [], {'max_length': '255'}),
            'obligee_street': ('django.db.models.fields.CharField', [], {'max_length': '255'}),
            'obligee_zip': ('django.db.models.fields.CharField', [], {'max_length': '10'})
        },
        u'inforequests.inforequest': {
            'Meta': {'object_name': 'Inforequest'},
            'applicant': ('django.db.models.fields.related.ForeignKey', [], {'to': u"orm['auth.User']"}),
            'applicant_city': ('django.db.models.fields.CharField', [], {'max_length': '255'}),
            'applicant_name': ('django.db.models.fields.CharField', [], {'max_length': '255'}),
            'applicant_street': ('django.db.models.fields.CharField', [], {'max_length': '255'}),
            'applicant_zip': ('django.db.models.fields.CharField', [], {'max_length': '10'}),
            'history': ('django.db.models.fields.related.OneToOneField', [], {'to': u"orm['inforequests.History']", 'unique': 'True'}),
            u'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'submission_date': ('django.db.models.fields.DateTimeField', [], {'auto_now_add': 'True', 'blank': 'True'}),
            'unique_email': ('django.db.models.fields.EmailField', [], {'unique': 'True', 'max_length': '255'})
        },
        u'inforequests.inforequestdraft': {
            'Meta': {'object_name': 'InforequestDraft'},
            'applicant': ('django.db.models.fields.related.ForeignKey', [], {'to': u"orm['auth.User']"}),
            'content': ('django.db.models.fields.TextField', [], {'blank': 'True'}),
            u'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'obligee': ('django.db.models.fields.related.ForeignKey', [], {'to': u"orm['obligees.Obligee']", 'null': 'True', 'blank': 'True'}),
            'subject': ('django.db.models.fields.CharField', [], {'max_length': '255', 'blank': 'True'})
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