# vim: expandtab
# -*- coding: utf-8 -*-
import gc

from django.db import models
from django.db.models.signals import post_save
from django.http import Http404
from django.test import TestCase

from poleno.utils.models import after_saved, join_lookup, FieldChoices, QuerySet
from poleno.utils.misc import decorate
from poleno.utils.test import created_instances

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

    objects = QuerySet.as_manager()

    class Meta:
        app_label = u'utils'

class TestModelsBulkModel(models.Model):
    name = models.CharField(blank=True, max_length=255)
    objects = QuerySet.as_manager()

    class Meta:
        app_label = u'utils'

    @decorate(prevent_bulk_create=False)
    def save(self, *args, **kwargs): # pragma: no cover
        super(TestModelsModel2, self).save(*args, **kwargs)

class TestModelsNoBulkModel(models.Model):
    name = models.CharField(blank=True, max_length=255)
    objects = QuerySet.as_manager()

    class Meta:
        app_label = u'utils'

    @decorate(prevent_bulk_create=True)
    def save(self, *args, **kwargs): # pragma: no cover
        super(TestModelsModel2, self).save(*args, **kwargs)


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
        def deffered(obj):
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
        def deffered(obj):
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
        def deffered_a(obj):
            counter[0] += 1

        @after_saved(obj)
        def deffered_b(obj):
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
        def deffered(obj1):
            counter[0] += 1

        self.assertEqual(counter, [0])
        obj2.name = u'obj2-changed'
        obj2.save()
        self.assertEqual(counter, [0])
        obj1.name = u'obj1-changed'
        obj1.save()
        self.assertEqual(counter, [1])

    def test_deffered_saves_instance_recursively(self):
        u"""
        Checks that the deffered function is called only once even if the instance is saved again
        while executing the deffered function. That is the deffered function is not called
        recursively.
        """

        obj = TestModelsModel(name=u'first')
        counter = [0]

        @after_saved(obj)
        def deffered(obj):
            counter[0] += 1
            obj.save()

        self.assertEqual(counter, [0])
        obj.save()
        self.assertEqual(counter, [1])

    def test_multiple_deffered_save_instance_recursively(self):
        u"""
        Checks that every deffered function is called only once even if the instance is saved again
        while executing the deffered functions.
        """
        obj = TestModelsModel(name=u'first')
        counter = [0, 0, 0]

        @after_saved(obj)
        def deffered_a(obj):
            counter[0] += 1
            obj.save()

        @after_saved(obj)
        def deffered_b(obj):
            counter[1] += 1
            obj.save()

        @after_saved(obj)
        def deffered_c(obj):
            counter[2] += 1
            obj.save()

        self.assertEqual(counter, [0, 0, 0])
        obj.save()
        self.assertEqual(counter, [1, 1, 1])

    def test_deffered_is_disconnected_after_instance_is_garbage_collected(self):
        obj = TestModelsModel(name=u'first')
        counter = [0]
        receivers = len(post_save.receivers)

        @after_saved(obj)
        def deffered(obj): # pragma: no cover
            counter[0] += 1

        self.assertEqual(len(post_save.receivers), receivers+1)
        obj = None
        gc.collect()
        self.assertEqual(counter, [0])
        self.assertEqual(len(post_save.receivers), receivers)

    def test_deffered_is_disconnected_after_instance_is_saved(self):
        obj = TestModelsModel(name=u'first')
        counter = [0]
        receivers = len(post_save.receivers)

        @after_saved(obj)
        def deffered(obj):
            counter[0] += 1

        self.assertEqual(len(post_save.receivers), receivers+1)
        obj.save()
        self.assertEqual(counter, [1])
        self.assertEqual(len(post_save.receivers), receivers)

class JoinLookupTest(TestCase):
    u"""
    Tests ``join_lookup()`` function.
    """

    def test(self):
        self.assertEqual(join_lookup(), u'')
        self.assertEqual(join_lookup(u'foo'), u'foo')
        self.assertEqual(join_lookup(u'foo', u'bar', u'bar'), u'foo__bar__bar')
        self.assertEqual(join_lookup(None, u'', None), u'')
        self.assertEqual(join_lookup(None, u'foo', None), u'foo')
        self.assertEqual(join_lookup(u'foo', None, u'bar', u'', u'bar'), u'foo__bar__bar')

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

    def test_duplicate_keys_raise_error(self):
        with self.assertRaisesMessage(ValueError, u'Duplicate choice key: 2'):
            FieldChoices((u'FIRST', 1, u'First'), (u'SECOND', 2, u'Second'), (u'THIRD', 2, u'Third'))
        with self.assertRaisesMessage(ValueError, u'Duplicate choice key: 1'):
            FieldChoices((u'FIRST', 1, u'First'), (u'GROUP', 1, ((u'AAA', 3, u'Aaa'), (u'BBB', 4, u'Bbb'))))
        with self.assertRaisesMessage(ValueError, u'Duplicate choice key: 3'):
            FieldChoices((u'FIRST', 1, u'First'), (u'GROUP', 3, ((u'AAA', 3, u'Aaa'), (u'BBB', 4, u'Bbb'))))

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

    def test_bulk_create_without_save_method(self):
        with created_instances(TestModelsModel.objects) as obj_set:
            TestModelsModel.objects.bulk_create([
                TestModelsModel(name=u'aaa'),
                TestModelsModel(name=u'bbb'),
                ])
        self.assertEqual(obj_set.count(), 2)

    def test_bulk_create_with_prevent_bulk_create_true(self):
        with created_instances(TestModelsBulkModel.objects) as obj_set:
            TestModelsBulkModel.objects.bulk_create([
                TestModelsBulkModel(name=u'aaa'),
                TestModelsBulkModel(name=u'bbb'),
                ])
        self.assertEqual(obj_set.count(), 2)

    def test_bulk_create_with_prevent_bulk_create_false(self):
        with created_instances(TestModelsNoBulkModel.objects) as obj_set:
            with self.assertRaisesMessage(ValueError, u"Can't bulk create TestModelsNoBulkModel"):
                TestModelsNoBulkModel.objects.bulk_create([
                    TestModelsNoBulkModel(name=u'aaa'),
                    TestModelsNoBulkModel(name=u'bbb'),
                    ])
        self.assertFalse(obj_set.exists())

    def test_get_or_404_with_single_result(self):
        res = TestModelsModel.objects.get_or_404(type=TestModelsModel.TYPES.WHITE)
        self.assertEqual(res, self.white)

    def test_get_or_404_with_no_results(self):
        with self.assertRaises(Http404):
            res = TestModelsModel.objects.get_or_404(type=TestModelsModel.TYPES.WHITE, pk=self.red.pk)

    def test_get_or_404_with_multiple_results(self):
        with self.assertRaises(TestModelsModel.MultipleObjectsReturned):
            res = TestModelsModel.objects.get_or_404(type=TestModelsModel.TYPES.BLACK)

    def test_apply(self):
        func = lambda q: q.filter(type=TestModelsModel.TYPES.BLACK)
        res = TestModelsModel.objects.apply(func)
        self.assertItemsEqual(res, [self.black1, self.black2])
