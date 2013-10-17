# -*- coding: utf-8 -*-
import datetime
from south.db import db
from south.v2 import SchemaMigration
from django.db import models


class Migration(SchemaMigration):

    def forwards(self, orm):
        # Adding model 'ChunkTranslation'
        db.create_table(u'chunks_chunk_translation', (
            (u'id', self.gf('django.db.models.fields.AutoField')(primary_key=True)),
            ('description', self.gf('django.db.models.fields.CharField')(max_length=255)),
            ('language_code', self.gf('django.db.models.fields.CharField')(max_length=15, db_index=True)),
            ('master', self.gf('django.db.models.fields.related.ForeignKey')(related_name='translations', null=True, to=orm['chunks.Chunk'])),
        ))
        db.send_create_signal(u'chunks', ['ChunkTranslation'])

        # Adding unique constraint on 'ChunkTranslation', fields ['language_code', 'master']
        db.create_unique(u'chunks_chunk_translation', ['language_code', 'master_id'])

        # Adding model 'Chunk'
        db.create_table(u'chunks_chunk', (
            (u'id', self.gf('django.db.models.fields.AutoField')(primary_key=True)),
            ('reverse_id', self.gf('django.db.models.fields.CharField')(unique=True, max_length=255)),
            ('content', self.gf('django.db.models.fields.related.ForeignKey')(to=orm['cms.Placeholder'], null=True)),
        ))
        db.send_create_signal(u'chunks', ['Chunk'])


    def backwards(self, orm):
        # Removing unique constraint on 'ChunkTranslation', fields ['language_code', 'master']
        db.delete_unique(u'chunks_chunk_translation', ['language_code', 'master_id'])

        # Deleting model 'ChunkTranslation'
        db.delete_table(u'chunks_chunk_translation')

        # Deleting model 'Chunk'
        db.delete_table(u'chunks_chunk')


    models = {
        u'chunks.chunk': {
            'Meta': {'object_name': 'Chunk'},
            'content': ('django.db.models.fields.related.ForeignKey', [], {'to': "orm['cms.Placeholder']", 'null': 'True'}),
            u'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'reverse_id': ('django.db.models.fields.CharField', [], {'unique': 'True', 'max_length': '255'})
        },
        u'chunks.chunktranslation': {
            'Meta': {'unique_together': "[('language_code', 'master')]", 'object_name': 'ChunkTranslation', 'db_table': "u'chunks_chunk_translation'"},
            'description': ('django.db.models.fields.CharField', [], {'max_length': '255'}),
            u'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'language_code': ('django.db.models.fields.CharField', [], {'max_length': '15', 'db_index': 'True'}),
            'master': ('django.db.models.fields.related.ForeignKey', [], {'related_name': "'translations'", 'null': 'True', 'to': u"orm['chunks.Chunk']"})
        },
        'cms.placeholder': {
            'Meta': {'object_name': 'Placeholder'},
            'default_width': ('django.db.models.fields.PositiveSmallIntegerField', [], {'null': 'True'}),
            u'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'slot': ('django.db.models.fields.CharField', [], {'max_length': '50', 'db_index': 'True'})
        }
    }

    complete_apps = ['chunks']