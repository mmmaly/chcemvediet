# -*- coding: utf-8 -*-
from south.utils import datetime_utils as datetime
from south.db import db
from south.v2 import SchemaMigration
from django.db import models


class Migration(SchemaMigration):

    def forwards(self, orm):
        # Deleting model 'History'
        db.delete_table(u'inforequests_history')

        # Adding model 'Paperwork'
        db.create_table(u'inforequests_paperwork', (
            (u'id', self.gf('django.db.models.fields.AutoField')(primary_key=True)),
            ('inforequest', self.gf('django.db.models.fields.related.ForeignKey')(to=orm['inforequests.Inforequest'])),
            ('obligee', self.gf('django.db.models.fields.related.ForeignKey')(to=orm['obligees.Obligee'])),
            ('historicalobligee', self.gf('django.db.models.fields.related.ForeignKey')(to=orm['obligees.HistoricalObligee'])),
            ('advanced_by', self.gf('django.db.models.fields.related.ForeignKey')(blank=True, related_name=u'advanced_to_set', null=True, to=orm['inforequests.Action'])),
        ))
        db.send_create_signal(u'inforequests', ['Paperwork'])

        # Deleting field 'Action.history'
        db.delete_column(u'inforequests_action', 'history_id')

        # Adding field 'Action.paperwork'
        db.add_column(u'inforequests_action', 'paperwork',
                      self.gf('django.db.models.fields.related.ForeignKey')(default=0, to=orm['inforequests.Paperwork']),
                      keep_default=False)

        # Deleting field 'ActionDraft.history'
        db.delete_column(u'inforequests_actiondraft', 'history_id')

        # Adding field 'ActionDraft.paperwork'
        db.add_column(u'inforequests_actiondraft', 'paperwork',
                      self.gf('django.db.models.fields.related.ForeignKey')(to=orm['inforequests.Paperwork'], null=True, blank=True),
                      keep_default=False)


    def backwards(self, orm):
        # Adding model 'History'
        db.create_table(u'inforequests_history', (
            ('obligee', self.gf('django.db.models.fields.related.ForeignKey')(to=orm['obligees.Obligee'])),
            ('historicalobligee', self.gf('django.db.models.fields.related.ForeignKey')(to=orm['obligees.HistoricalObligee'])),
            ('inforequest', self.gf('django.db.models.fields.related.ForeignKey')(to=orm['inforequests.Inforequest'])),
            ('advanced_by', self.gf('django.db.models.fields.related.ForeignKey')(related_name=u'advanced_to_set', null=True, to=orm['inforequests.Action'], blank=True)),
            (u'id', self.gf('django.db.models.fields.AutoField')(primary_key=True)),
        ))
        db.send_create_signal(u'inforequests', ['History'])

        # Deleting model 'Paperwork'
        db.delete_table(u'inforequests_paperwork')

        # Adding field 'Action.history'
        db.add_column(u'inforequests_action', 'history',
                      self.gf('django.db.models.fields.related.ForeignKey')(default=0, to=orm['inforequests.History']),
                      keep_default=False)

        # Deleting field 'Action.paperwork'
        db.delete_column(u'inforequests_action', 'paperwork_id')

        # Adding field 'ActionDraft.history'
        db.add_column(u'inforequests_actiondraft', 'history',
                      self.gf('django.db.models.fields.related.ForeignKey')(to=orm['inforequests.History'], null=True, blank=True),
                      keep_default=False)

        # Deleting field 'ActionDraft.paperwork'
        db.delete_column(u'inforequests_actiondraft', 'paperwork_id')


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
            'Meta': {'ordering': "[u'effective_date', u'pk']", 'object_name': 'Action'},
            'content': ('django.db.models.fields.TextField', [], {'blank': 'True'}),
            'deadline': ('django.db.models.fields.IntegerField', [], {'null': 'True', 'blank': 'True'}),
            'disclosure_level': ('django.db.models.fields.SmallIntegerField', [], {'null': 'True', 'blank': 'True'}),
            'effective_date': ('django.db.models.fields.DateField', [], {}),
            'email': ('django.db.models.fields.related.OneToOneField', [], {'to': u"orm['mail.Message']", 'unique': 'True', 'null': 'True', 'blank': 'True'}),
            'extension': ('django.db.models.fields.IntegerField', [], {'null': 'True', 'blank': 'True'}),
            u'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'last_deadline_reminder': ('django.db.models.fields.DateTimeField', [], {'null': 'True', 'blank': 'True'}),
            'paperwork': ('django.db.models.fields.related.ForeignKey', [], {'to': u"orm['inforequests.Paperwork']"}),
            'refusal_reason': ('django.db.models.fields.SmallIntegerField', [], {'null': 'True', 'blank': 'True'}),
            'subject': ('django.db.models.fields.CharField', [], {'max_length': '255', 'blank': 'True'}),
            'type': ('django.db.models.fields.SmallIntegerField', [], {})
        },
        u'inforequests.actiondraft': {
            'Meta': {'ordering': "[u'pk']", 'object_name': 'ActionDraft'},
            'content': ('django.db.models.fields.TextField', [], {'blank': 'True'}),
            'deadline': ('django.db.models.fields.IntegerField', [], {'null': 'True', 'blank': 'True'}),
            'disclosure_level': ('django.db.models.fields.SmallIntegerField', [], {'null': 'True', 'blank': 'True'}),
            'effective_date': ('django.db.models.fields.DateField', [], {'null': 'True', 'blank': 'True'}),
            u'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'inforequest': ('django.db.models.fields.related.ForeignKey', [], {'to': u"orm['inforequests.Inforequest']"}),
            'obligee_set': ('django.db.models.fields.related.ManyToManyField', [], {'to': u"orm['obligees.Obligee']", 'symmetrical': 'False'}),
            'paperwork': ('django.db.models.fields.related.ForeignKey', [], {'to': u"orm['inforequests.Paperwork']", 'null': 'True', 'blank': 'True'}),
            'refusal_reason': ('django.db.models.fields.SmallIntegerField', [], {'null': 'True', 'blank': 'True'}),
            'subject': ('django.db.models.fields.CharField', [], {'max_length': '255', 'blank': 'True'}),
            'type': ('django.db.models.fields.SmallIntegerField', [], {})
        },
        u'inforequests.inforequest': {
            'Meta': {'ordering': "[u'submission_date', u'pk']", 'object_name': 'Inforequest'},
            'applicant': ('django.db.models.fields.related.ForeignKey', [], {'to': u"orm['auth.User']"}),
            'applicant_city': ('django.db.models.fields.CharField', [], {'max_length': '255'}),
            'applicant_name': ('django.db.models.fields.CharField', [], {'max_length': '255'}),
            'applicant_street': ('django.db.models.fields.CharField', [], {'max_length': '255'}),
            'applicant_zip': ('django.db.models.fields.CharField', [], {'max_length': '10'}),
            'closed': ('django.db.models.fields.BooleanField', [], {'default': 'False'}),
            'email_set': ('django.db.models.fields.related.ManyToManyField', [], {'to': u"orm['mail.Message']", 'through': u"orm['inforequests.InforequestEmail']", 'symmetrical': 'False'}),
            u'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'last_undecided_email_reminder': ('django.db.models.fields.DateTimeField', [], {'null': 'True', 'blank': 'True'}),
            'submission_date': ('django.db.models.fields.DateField', [], {'auto_now_add': 'True', 'blank': 'True'}),
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
        u'inforequests.inforequestemail': {
            'Meta': {'object_name': 'InforequestEmail'},
            'email': ('django.db.models.fields.related.ForeignKey', [], {'to': u"orm['mail.Message']"}),
            u'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'inforequest': ('django.db.models.fields.related.ForeignKey', [], {'to': u"orm['inforequests.Inforequest']"}),
            'type': ('django.db.models.fields.SmallIntegerField', [], {})
        },
        u'inforequests.paperwork': {
            'Meta': {'ordering': "[u'historicalobligee__name', u'pk']", 'object_name': 'Paperwork'},
            'advanced_by': ('django.db.models.fields.related.ForeignKey', [], {'blank': 'True', 'related_name': "u'advanced_to_set'", 'null': 'True', 'to': u"orm['inforequests.Action']"}),
            'historicalobligee': ('django.db.models.fields.related.ForeignKey', [], {'to': u"orm['obligees.HistoricalObligee']"}),
            u'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'inforequest': ('django.db.models.fields.related.ForeignKey', [], {'to': u"orm['inforequests.Inforequest']"}),
            'obligee': ('django.db.models.fields.related.ForeignKey', [], {'to': u"orm['obligees.Obligee']"})
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
        u'obligees.historicalobligee': {
            'Meta': {'ordering': "(u'-history_date', u'-history_id')", 'object_name': 'HistoricalObligee'},
            'city': ('django.db.models.fields.CharField', [], {'max_length': '255'}),
            'emails': ('django.db.models.fields.CharField', [], {'max_length': '1024'}),
            u'history_date': ('django.db.models.fields.DateTimeField', [], {}),
            u'history_id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            u'history_type': ('django.db.models.fields.CharField', [], {'max_length': '1'}),
            u'history_user': ('django.db.models.fields.related.ForeignKey', [], {'to': u"orm['auth.User']", 'null': 'True'}),
            u'id': ('django.db.models.fields.IntegerField', [], {'db_index': 'True', 'blank': 'True'}),
            'name': ('django.db.models.fields.CharField', [], {'max_length': '255'}),
            'slug': ('django.db.models.fields.SlugField', [], {'max_length': '255'}),
            'status': ('django.db.models.fields.SmallIntegerField', [], {}),
            'street': ('django.db.models.fields.CharField', [], {'max_length': '255'}),
            'zip': ('django.db.models.fields.CharField', [], {'max_length': '10'})
        },
        u'obligees.obligee': {
            'Meta': {'ordering': "[u'name']", 'object_name': 'Obligee'},
            'city': ('django.db.models.fields.CharField', [], {'max_length': '255'}),
            'emails': ('django.db.models.fields.CharField', [], {'max_length': '1024'}),
            u'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'name': ('django.db.models.fields.CharField', [], {'max_length': '255'}),
            'slug': ('django.db.models.fields.SlugField', [], {'max_length': '255'}),
            'status': ('django.db.models.fields.SmallIntegerField', [], {}),
            'street': ('django.db.models.fields.CharField', [], {'max_length': '255'}),
            'zip': ('django.db.models.fields.CharField', [], {'max_length': '10'})
        }
    }

    complete_apps = ['inforequests']