# vim: expandtab
# -*- coding: utf-8 -*-
from django.db import migrations


class RenameOrAddIndex(migrations.RenameIndex):
    u"""
    ``RenameIndex(old_fields=...)`` renames an index created by the ``index_together`` option
    of an earlier migration. Django 5.1+ ignores ``index_together`` when creating tables, so on
    a freshly created database (tests, new installations) there is no index to rename. In that
    case the index is created instead. Existing databases are renamed as usual.
    """

    def database_forwards(self, app_label, schema_editor, from_state, to_state):
        if self.old_fields:
            from_model = from_state.apps.get_model(app_label, self.model_name)
            columns = [from_model._meta.get_field(field).column for field in self.old_fields]
            matching = schema_editor._constraint_names(from_model, column_names=columns,
                    index=True)
            if not matching:
                to_model = to_state.apps.get_model(app_label, self.model_name)
                index = to_model._meta.indexes[[i.name for i in to_model._meta.indexes]
                        .index(self.new_name)]
                schema_editor.add_index(to_model, index)
                return
        super(RenameOrAddIndex, self).database_forwards(
                app_label, schema_editor, from_state, to_state)
