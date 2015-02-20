# vim: expandtab
# -*- coding: utf-8 -*-
import weakref

from django.db import models
from django.db.models.signals import post_save
from django.db.models.constants import LOOKUP_SEP
from django.shortcuts import get_object_or_404

from .misc import Bunch

class _Receiver(object):
    def __init__(self, model, func):
        self.sender = model.__class__
        self.weak = weakref.ref(model, lambda w: self.disconnect())
        self.func = func
        self.connected = False

    def connect(self):
        post_save.connect(self, sender=self.sender, weak=False, dispatch_uid=id(self))
        self.connected = True

    def disconnect(self):
        post_save.disconnect(sender=self.sender, dispatch_uid=id(self))
        self.connected = False

    def __call__(self, sender, instance, **kwargs):
        model = self.weak()
        if model and self.connected and instance is model:
            self.disconnect()
            self.func(model)

def after_saved(model):
    u"""
    Decorator that registers a function to be called after the ``model`` instance is saved. The
    function is called only once, when the instance is saved for the first time, then it is
    unregistered. If the instance is never saved the function is never called. The decorator keeps
    only a weak reference to the instance, so after the instance is garbage collected the function
    is unregistered.

    It is useful if you need to use a reference to a model that is not saved yet, but it will be
    soon. You cannot make a reference to such model now, because it has no ``pk`` defined yet, you
    must wait until it's saved and has defined its ``pk``.

    Example:
        def save_book(author):
            book = Book(title="The Book")

            if author.pk is None:
                @after_saved(author)
                def deferred(author):
                    book.author = author
                    book.save()
            else:
                book.author = author
                book.save()
    """
    def _decorator(func):
        receiver = _Receiver(model, func)
        receiver.connect()
        return func
    return _decorator

def join_lookup(*args):
    u"""
    Joins Django field lookup path skipping empty parts. For instance:
        join_lookup('foo', None, 'bar', 'bar') -> 'foo__bar__bar'
        join_lookup('foo') -> 'foo'
        join_lookup(None) -> ''
    """
    return LOOKUP_SEP.join(a for a in args if a)

class FieldChoices(object):
    u"""
    Simple container for django model field choices following DRY principle.

    Example:
        class Mail(models.Model):
            STATUSES = FieldChoices(
                ('UNKNOWN', 1, _('Unknown')),
                ('DELIVERED', 2, _('Delivered')),
                ('RETURNED', 3, _('Returned')),
                ('LOST', 4, _('Lost')),
                )
            status = models.SmallIntegerField(choices=STATUSES._choices, verbose_name=_(u'Status'))

        mail = Mail()
        mail.status = mail.STATUSES.DELIVERED
        mail.STATUSES._inverse[2] == 'DELIVERED'
    """
    def __init__(self, *args):
        choices = []
        inverse = {}
        for choice_name, choice_key, choice_value in args:
            if choice_key in inverse:
                raise ValueError(u'Duplicate choice key: %r' % choice_key)
            inverse[choice_key] = choice_name
            if isinstance(choice_value, (list, tuple)): # It's a choice group
                group = []
                bunch = Bunch()
                for group_name, group_key, group_value in choice_value:
                    if group_key in inverse:
                        raise ValueError(u'Duplicate choice key: %r' % choice_key)
                    inverse[group_key] = u'%s.%s' % (choice_name, group_name)
                    group.append((group_key, group_value))
                    setattr(bunch, group_name, group_key)
                choices.append((choice_key, group))
                setattr(self, choice_name, bunch)
            else:
                choices.append((choice_key, choice_value))
                setattr(self, choice_name, choice_key)
        self._choices = choices
        self._inverse = inverse

class QuerySet(models.query.QuerySet):
    u"""
    ``QuerySet`` with common custom methods.
    """

    def get_or_404(self, *args, **kwargs):
        u"""
        Uses ``get()`` to return an object, or raises a ``Http404`` exception if the object does
        not exist. Like with ``get()``, an ``MultipleObjectsReturned`` will be raised if more than
        one object is found.
        """
        return get_object_or_404(self, *args, **kwargs)

    def apply(self, func):
        u"""
        Applies ``func`` on the queryset.
        """
        return func(self)
