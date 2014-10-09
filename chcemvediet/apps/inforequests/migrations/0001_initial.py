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
            ('applicant_name', self.gf('django.db.models.fields.CharField')(max_length=255)),
            ('applicant_street', self.gf('django.db.models.fields.CharField')(max_length=255)),
            ('applicant_city', self.gf('django.db.models.fields.CharField')(max_length=255)),
            ('applicant_zip', self.gf('django.db.models.fields.CharField')(max_length=10)),
            ('unique_email', self.gf('django.db.models.fields.EmailField')(unique=True, max_length=255)),
            ('submission_date', self.gf('django.db.models.fields.DateField')(auto_now_add=True, blank=True)),
            ('closed', self.gf('django.db.models.fields.BooleanField')(default=False)),
            ('last_undecided_email_reminder', self.gf('django.db.models.fields.DateTimeField')(null=True, blank=True)),
        ))
        db.send_create_signal(u'inforequests', ['Inforequest'])

        # Adding model 'InforequestEmail'
        db.create_table(u'inforequests_inforequestemail', (
            (u'id', self.gf('django.db.models.fields.AutoField')(primary_key=True)),
            ('inforequest', self.gf('django.db.models.fields.related.ForeignKey')(to=orm['inforequests.Inforequest'])),
            ('email', self.gf('django.db.models.fields.related.ForeignKey')(to=orm['mail.Message'])),
            ('type', self.gf('django.db.models.fields.SmallIntegerField')()),
        ))
        db.send_create_signal(u'inforequests', ['InforequestEmail'])

        # Adding model 'Paperwork'
        db.create_table(u'inforequests_paperwork', (
            (u'id', self.gf('django.db.models.fields.AutoField')(primary_key=True)),
            ('inforequest', self.gf('django.db.models.fields.related.ForeignKey')(to=orm['inforequests.Inforequest'])),
            ('obligee', self.gf('django.db.models.fields.related.ForeignKey')(to=orm['obligees.Obligee'])),
            ('historicalobligee', self.gf('django.db.models.fields.related.ForeignKey')(to=orm['obligees.HistoricalObligee'])),
            ('advanced_by', self.gf('django.db.models.fields.related.ForeignKey')(blank=True, related_name=u'advanced_to_set', null=True, to=orm['inforequests.Action'])),
        ))
        db.send_create_signal(u'inforequests', ['Paperwork'])

        # Adding model 'Action'
        db.create_table(u'inforequests_action', (
            (u'id', self.gf('django.db.models.fields.AutoField')(primary_key=True)),
            ('paperwork', self.gf('django.db.models.fields.related.ForeignKey')(to=orm['inforequests.Paperwork'])),
            ('email', self.gf('django.db.models.fields.related.OneToOneField')(to=orm['mail.Message'], unique=True, null=True, blank=True)),
            ('type', self.gf('django.db.models.fields.SmallIntegerField')()),
            ('subject', self.gf('django.db.models.fields.CharField')(max_length=255, blank=True)),
            ('content', self.gf('django.db.models.fields.TextField')(blank=True)),
            ('effective_date', self.gf('django.db.models.fields.DateField')()),
            ('deadline', self.gf('django.db.models.fields.IntegerField')(null=True, blank=True)),
            ('extension', self.gf('django.db.models.fields.IntegerField')(null=True, blank=True)),
            ('disclosure_level', self.gf('django.db.models.fields.SmallIntegerField')(null=True, blank=True)),
            ('refusal_reason', self.gf('django.db.models.fields.SmallIntegerField')(null=True, blank=True)),
            ('last_deadline_reminder', self.gf('django.db.models.fields.DateTimeField')(null=True, blank=True)),
        ))
        db.send_create_signal(u'inforequests', ['Action'])

        # Adding model 'ActionDraft'
        db.create_table(u'inforequests_actiondraft', (
            (u'id', self.gf('django.db.models.fields.AutoField')(primary_key=True)),
            ('inforequest', self.gf('django.db.models.fields.related.ForeignKey')(to=orm['inforequests.Inforequest'])),
            ('paperwork', self.gf('django.db.models.fields.related.ForeignKey')(to=orm['inforequests.Paperwork'], null=True, blank=True)),
            ('type', self.gf('django.db.models.fields.SmallIntegerField')()),
            ('subject', self.gf('django.db.models.fields.CharField')(max_length=255, blank=True)),
            ('content', self.gf('django.db.models.fields.TextField')(blank=True)),
            ('effective_date', self.gf('django.db.models.fields.DateField')(null=True, blank=True)),
            ('deadline', self.gf('django.db.models.fields.IntegerField')(null=True, blank=True)),
            ('disclosure_level', self.gf('django.db.models.fields.SmallIntegerField')(null=True, blank=True)),
            ('refusal_reason', self.gf('django.db.models.fields.SmallIntegerField')(null=True, blank=True)),
        ))
        db.send_create_signal(u'inforequests', ['ActionDraft'])

        # Adding M2M table for field obligee_set on 'ActionDraft'
        m2m_table_name = db.shorten_name(u'inforequests_actiondraft_obligee_set')
        db.create_table(m2m_table_name, (
            ('id', models.AutoField(verbose_name='ID', primary_key=True, auto_created=True)),
            ('actiondraft', models.ForeignKey(orm[u'inforequests.actiondraft'], null=False)),
            ('obligee', models.ForeignKey(orm[u'obligees.obligee'], null=False))
        ))
        db.create_unique(m2m_table_name, ['actiondraft_id', 'obligee_id'])


    def backwards(self, orm):
        # Deleting model 'InforequestDraft'
        db.delete_table(u'inforequests_inforequestdraft')

        # Deleting model 'Inforequest'
        db.delete_table(u'inforequests_inforequest')

        # Deleting model 'InforequestEmail'
        db.delete_table(u'inforequests_inforequestemail')

        # Deleting model 'Paperwork'
        db.delete_table(u'inforequests_paperwork')

        # Deleting model 'Action'
        db.delete_table(u'inforequests_action')

        # Deleting model 'ActionDraft'
        db.delete_table(u'inforequests_actiondraft')

        # Removing M2M table for field obligee_set on 'ActionDraft'
        db.delete_table(db.shorten_name(u'inforequests_actiondraft_obligee_set'))


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