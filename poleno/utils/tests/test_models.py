# vim: expandtab
# -*- coding: utf-8 -*-
from django.db import models
from django.http import Http404
from django.test import TestCase

from poleno.utils.models import after_saved, FieldChoices, QuerySet

class TestModelsModelQuerySet(QuerySet):
    def black(self):
        return self.filter(type=TestModelsModel.TYPES.BLACK)
    def red(self):
        return self.filter(type=TestModelsModel.TYPES.RGB.RED)
    def rgb(self):
        return self.filter(type__in=[TestModelsModel.TYPES.RGB.RED, TestModelsModel.TYPES.RGB.GREEN, TestModelsModel.TYPES.RGB.BLUE])
    def _private(self):
        pass

class TestModelsModel(models.Model):
    name = models.CharField(blank=True, max_length=255)

    TYPES = FieldChoices(
            (u'BLACK', 1, u'Black'),
            (u'WHITE', 2, u'White'),
            (u'RGB', 3, (
                (u'RED', 4, u'Red'),
                (u'GREEN', 5, u'Green'),
                (u'BLUE', 6, u'Blue'),
                )),
            )
    type = models.SmallIntegerField(choices=TYPES._choices, default=TYPES.BLACK)

    objects = TestModelsModelQuerySet.as_manager()

    class Meta:
        app_label = u'utils'


class AfterSavedTest(TestCase):
    u"""
    Tests ``@after_saved`` decorator. Checks that the deffered function is
    called only once, after the object is saved for the first time.
    """

    def setUp(self):
        self.obj1 = TestModelsModel.objects.create(name=u'obj1')
        self.obj2 = TestModelsModel.objects.create(name=u'obj2')

    def test_after_new_instance_saved(self):
        u"""
        Checks that the deffered function is called when a new object is created.
        """
        obj = TestModelsModel(name=u'first')
        counter = [0]

        @after_saved(obj)
        def deffered():
            counter[0] += 1

        self.assertEqual(counter, [0])
        obj.save()
        self.assertEqual(counter, [1])
        obj.name = u'second'
        obj.save()
        self.assertEqual(counter, [1])

    def test_after_altered_instance_saved(self):
        u"""
        Checks that the deffered function is called when an already existing object is altered and
        saved.
        """
        obj = TestModelsModel.objects.first()
        counter = [0]

        @after_saved(obj)
        def deffered():
            counter[0] += 1

        self.assertEqual(counter, [0])
        obj.name = u'second'
        obj.save()
        self.assertEqual(counter, [1])
        obj.name = u'third'
        obj.save()
        self.assertEqual(counter, [1])

    def test_multiple_deffered_functions(self):
        u"""
        Checks that if there are two deffered functions for one instance, both deffered functions
        are called when the instance is saved.
        """
        obj = TestModelsModel.objects.create(name=u'first')
        counter = [0, 0]

        @after_saved(obj)
        def deffered_a():
            counter[0] += 1

        @after_saved(obj)
        def deffered_b():
            counter[1] += 1

        self.assertEqual(counter, [0, 0])
        obj.save()
        self.assertEqual(counter, [1, 1])

    def test_multiple_instances(self):
        u"""
        Checks that the deffered funstion is not called when another instance of the same model is
        saved.
        """
        obj1 = TestModelsModel.objects.create(name=u'obj1')
        obj2 = TestModelsModel.objects.create(name=u'obj2')
        counter = [0]

        @after_saved(obj1)
        def deffered():
            counter[0] += 1

        self.assertEqual(counter, [0])
        obj2.name = u'obj2-changed'
        obj2.save()
        self.assertEqual(counter, [0])
        obj1.name = u'obj1-changed'
        obj1.save()
        self.assertEqual(counter, [1])

    def test_instance_saved_in_deffered_function(self):
        u"""
        Checks that the deffered function is called only once event if the instance is saved again
        while executing the deffered function. That is the deffered function is not called
        recursively.
        """

        obj = TestModelsModel(name=u'first')
        counter = [0]

        @after_saved(obj)
        def deffered():
            counter[0] += 1
            obj.save()

        self.assertEqual(counter, [0])
        obj.save()
        self.assertEqual(counter, [1])

class FieldChoicesTest(TestCase):
    u"""
    Tests ``FieldChoices`` by hand without using model. Checks if choice constants, inverse
    mappings and ``_choice`` lists are set corectly. Also checks if raises exception if used
    invalid choice constant.
    """

    def test_simple_choices(self):
        res = FieldChoices((u'FIRST', 1, u'First'), (u'SECOND', 2, u'Second'), (u'THIRD', 3, u'Third'))
        self.assertEqual(res.FIRST, 1)
        self.assertEqual(res.SECOND, 2)
        self.assertEqual(res.THIRD, 3)
        self.assertEqual(res._inverse[res.FIRST], u'FIRST')
        self.assertEqual(res._inverse[res.SECOND], u'SECOND')
        self.assertEqual(res._inverse[res.THIRD], u'THIRD')
        self.assertEqual(res._choices, [(1, u'First'), (2, u'Second'), (3, u'Third')])

    def test_choices_with_groups(self):
        res = FieldChoices((u'FIRST', 1, u'First'), (u'GROUP', 2, ((u'AAA', 3, u'Aaa'), (u'BBB', 4, u'Bbb'))))
        self.assertEqual(res.FIRST, 1)
        self.assertEqual(res.GROUP.AAA, 3)
        self.assertEqual(res.GROUP.BBB, 4)
        self.assertEqual(res._inverse[res.FIRST], u'FIRST')
        self.assertEqual(res._inverse[res.GROUP.AAA], u'GROUP.AAA')
        self.assertEqual(res._inverse[res.GROUP.BBB], u'GROUP.BBB')
        self.assertEqual(res._choices, [(1, u'First'), (2, [(3, u'Aaa'), (4, u'Bbb')])])

    def test_empty_choices(self):
        res = FieldChoices()
        self.assertEqual(res._choices, [])
        with self.assertRaises(AttributeError):
            res.FIRST

class QuerySetTest(TestCase):
    u"""
    Tests ``FieldChoices`` and custom ``QuerySet` on testing ``TestModelsModel``.
    """

    def setUp(self):
        self.black1 = TestModelsModel.objects.create(name=u'black1', type=TestModelsModel.TYPES.BLACK)
        self.black2 = TestModelsModel.objects.create(name=u'black2', type=TestModelsModel.TYPES.BLACK)
        self.white = TestModelsModel.objects.create(name=u'white', type=TestModelsModel.TYPES.WHITE)
        self.red = TestModelsModel.objects.create(name=u'red', type=TestModelsModel.TYPES.RGB.RED)
        self.blue = TestModelsModel.objects.create(name=u'blue', type=TestModelsModel.TYPES.RGB.BLUE)

    def test_single_queryset_method(self):
        res = TestModelsModel.objects.black()
        self.assertItemsEqual(res, [self.black1, self.black2])

    def test_chained_queryset_methods(self):
        res = TestModelsModel.objects.all().rgb().all()
        self.assertItemsEqual(res, [self.red, self.blue])

    def test_queryset_with_single_result(self):
        res = TestModelsModel.objects.rgb().red()
        self.assertItemsEqual(res, [self.red])

    def test_queryset_with_no_results(self):
        res = TestModelsModel.objects.rgb().black()
        self.assertItemsEqual(res, [])

    def test_object_manager_private_attributes(self):
        u"""
        Checks that private methods/attributes of the QuerySet may not be accessed from their
        object managers.
        """
        # Private methods on the object managers are not accessible.
        with self.assertRaises(AttributeError):
            TestModelsModel.objects._private()
        # But the same method on the QuerySet is accessible.
        TestModelsModel.objects.all()._private()

    def test_get_or_404_with_single_result(self):
        res = TestModelsModel.objects.get_or_404(type=TestModelsModel.TYPES.WHITE)
        self.assertEqual(res, self.white)

    def test_get_or_404_with_no_results(self):
        with self.assertRaises(Http404):
            res = TestModelsModel.objects.get_or_404(type=TestModelsModel.TYPES.WHITE, pk=self.red.pk)

    def test_get_or_404_with_multiple_results(self):
        with self.assertRaises(TestModelsModel.MultipleObjectsReturned):
            res = TestModelsModel.objects.get_or_404(type=TestModelsModel.TYPES.BLACK)

    def test_get_display_of_field_with_choices(self):
        res = TestModelsModel.objects.get(pk=self.white.pk)
        self.assertEqual(res.get_type_display(), u'White')
