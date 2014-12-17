# vim: expandtab
# -*- coding: utf-8 -*-

from django.db import models
from django.db.models.signals import post_save
from django.shortcuts import get_object_or_404

from .misc import Bunch

def after_saved(model):
    u"""
    Decorator which registers given function to be called after the ``model`` instance is saved
    using ``post_save`` signal. The function is called just once, when the instance is saved for
    the first time, then it is unregistered. If the ``model`` instance is never saved the function
    is never called.

    It is useful if you need to use a reference to a model that is not saved yet, but it will be
    soon. You cannot make a reference to such model now, because it has no ``pk`` defined yet, you
    must wait until it's saved and has defined its ``pk``.

    Example:
        def save_book(author):
            book = Book(title="The Book")

            if author.pk is None:
                @after_saved(author)
                def deferred:
                    book.author = author
                    book.save()
            else:
                book.author = author
                book.save()
    """
    # FIXME: What if ``model`` never gets saved? We should keep just a weak reference to it and
    # disconnect when the object is destroyed without saving. We should also make sure the deffered
    # function ``func`` does not keep reference to this object. It seems that nested functions
    # without free variables does not create closures, and so does not keep references to outer
    # function local variables. But I'm not sure.
    def _decorator(func):
        uid=(id(func), id(model))
        def receiver(sender, instance, **kwargs):
            if instance is model:
                post_save.disconnect(sender=model.__class__, dispatch_uid=uid)
                func()
        post_save.connect(receiver, sender=model.__class__, weak=False, dispatch_uid=uid)
        return func
    return _decorator

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
    Wrapper to simplify adding custom query methods for defined models. For every model you can
    inherit this ``QuerySet`` and add your query methods. This class defines several handy shortcut
    methods as well. The new methods work for models, as well as for forward and backward
    relations.

    Example:

        class ArticleQuerySet(QuerySet):
            def published(self):
                return self.filter(published=True)
            def popular(self):
                return self.filter(popular=True)

        class Author(Model):
            name = models.CharField(...)

        class Article(Model):
            author = models.ForeignKey(Author, ...)
            published = BooleanField(...)
            popular = BooleanField(...)

            objects = ArticleQuerySet.as_manager()

        Article.objects.published().popular()
        Author.objects.get(...).article_set.published()

    Source:
        http://adam.gomaa.us/blog/2009/feb/16/subclassing-django-querysets/index.html
        http://stackoverflow.com/questions/4576622/in-django-can-you-add-a-method-to-querysets#answer-7961021

    In contrast to the sources, we create new ``QuerySetManager`` class dynamically for every
    model. Otherwise Django wouldn't be able to inherit from it properly and dynamically create
    ``RelatedManager`` for forward and backward realtions.
    """

    @classmethod
    def as_manager(cls):

        class QuerySetManager(models.Manager):
            use_for_related_fields = True

            def get_query_set(self):
                return cls(self.model)

            def __getattr__(self, name, *args):
                if name.startswith(u'_'):
                    # We don't let the object manager access private methods/attributes of the
                    # queryset. For instance, according to:
                    #     https://djangosnippets.org/snippets/734/#c903
                    # Pickle library goes crazy if QuerySet ``__getstate__`` or ``__setstate__``
                    # can be accessed from the object manager.
                    raise AttributeError
                return getattr(self.get_query_set(), name, *args)

        return QuerySetManager()

    def get_or_404(self, *args, **kwargs):
        u"""
        Uses ``get()`` to return an object, or raises a ``Http404`` exception if the object does
        not exist. Like with ``get()``, an ``MultipleObjectsReturned`` will be raised if more than
        one object is found.
        """
        return get_object_or_404(self, *args, **kwargs)
