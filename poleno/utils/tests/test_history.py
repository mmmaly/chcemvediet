# vim: expandtab
# -*- coding: utf-8 -*-
from django.db import models, connection
from django.test import TestCase

from poleno.utils.history import register_history

@register_history
class RegisterHistoryTestModel(models.Model):
    name = models.CharField(blank=True, max_length=255)

    class Meta:
        app_label = u'utils'
        verbose_name = u'test'

@register_history(manager_name=u'hist')
class RegisterHistoryWithArgumentsTestModel(models.Model):
    name = models.CharField(blank=True, max_length=255)

    class Meta:
        app_label = u'utils'
        verbose_name = u'test'


class RegisterHistoryTest(TestCase):
    u"""
    Tests ``@register_history`` decorator without arguments. Checks that the historical model and
    its db table are created, and that the historical model tracks the model history.
    """
    model = RegisterHistoryTestModel
    historicalmodel = HistoricalRegisterHistoryTestModel
    historicalmodel_table = u'utils_historicalregisterhistorytestmodel'
    history_attribute = u'history'

    def test_history_model_created(self):
        created_models = models.get_models(include_auto_created=True)
        self.assertIn(self.historicalmodel, created_models)

    def test_history_model_db_table_created(self):
        tables = connection.introspection.table_names()
        self.assertIn(self.historicalmodel_table, tables)

    def test_history_model_contains_all_model_fields(self):
        for field in self.model._meta.fields:
            self.assertIn(field, self.historicalmodel._meta.fields)

    def test_history_model_records_changes(self):
        obj = self.model.objects.create(name=u'first')
        obj.name = u'changed'
        obj.save()

        history = getattr(obj, self.history_attribute).all()
        self.assertEqual(len(history), 2)
        self.assertEqual(history[0].name, u'changed')
        self.assertEqual(history[1].name, u'first')

class RegisterHistoryWithArgumentsTest(RegisterHistoryTest):
    u"""
    Tests ``@register_history`` decorator with arguments. Checks that its arguments are passed to
    the actual ``simple_history.register()`` function.
    """
    model = RegisterHistoryWithArgumentsTestModel
    historicalmodel = HistoricalRegisterHistoryWithArgumentsTestModel
    historicalmodel_table = u'utils_historicalregisterhistorywithargumentstestmodel'
    history_attribute = u'hist'
