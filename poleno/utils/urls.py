# vim: expandtab
# -*- coding: utf-8 -*-
from collections import defaultdict

from django.urls import get_urlconf, get_resolver, reverse as django_reverse
from django.contrib.sites.models import Site


reverse_adaptors = defaultdict(list)

def reverse_adaptor(viewname, argname):
    u"""
    See ``reverse()`` below.
    """
    def actual_decorator(func):
        reverse_adaptors[viewname].append((argname, func))
        return func
    return actual_decorator

def reverse(viewname, urlconf=None, args=None, kwargs=None, current_app=None):
    u"""
    Django ``reverse()`` expects exactly the same arguments as parsed from url. However, sometimes
    it is more convenient to call ``reverse()`` with complex objects that can be reduced to url
    arguments automatically. Suppose we have model "Author" that is represented by its "pk" and
    "name" in the url:

        url(r'^/(?P<name>\w+)/(?P<pk>\d+)/$', author_view, name='detail')

    Instead of writing:

        reverse('detail', kwargs=dict(name=author.name, pk=author.pk))

        {% url 'detail' name=author.name pk=author.pk %}

    We may write simply:

        reverse('detail', kwargs=dict(author=author))

        {% url 'detail' author=author %}

    If we register the following reverse adaptor:

        @reverse_adaptor('detail', 'author')
        def author_adaptor(author):
            return dict(name=author.name, pk=author.pk)

    Further, this function strips ``kwargs`` of all None values and ``args`` of all trailing None
    values as Django ``reverse()`` breaks if given None as an argument. Django resolver may
    populate arguments with None when parsing certain urls, therefore it's not possible to
    recostruct such urls with Django ``reverse()``. Unfortunatelly, if None occurs in the middle of
    ``args`` there is no way to fix it.
    """
    # Make sure urls were included. Otherwise the adaptors don't have to be registered yet if this
    # is the first call to the resolver.
    get_resolver(urlconf or get_urlconf())._populate()

    for argname, adaptor in reverse_adaptors[viewname]:
        if kwargs and argname in kwargs:
            kwargs.update(adaptor(kwargs.pop(argname)))

    if args is not None:
        while args and args[-1] is None:
            args = args[:-1]
    if kwargs is not None:
        kwargs = dict((k, v) for k, v in kwargs.iteritems() if v is not None)
    return django_reverse(viewname, urlconf, args, kwargs, current_app)

def complete_url(path, secure=False):
    u"""
    Returns complete url using given path and current site instance.
    """
    protocol = u'https' if secure else u'http'
    domain = Site.objects.get_current().domain
    return u'{0}://{1}{2}'.format(protocol, domain, path)

def complete_reverse(viewname, *args, **kwargs):
    u"""
    Returns complete url using django ``reverse`` function and current site instance.
    """
    secure = kwargs.pop(u'secure', False)
    anchor = kwargs.pop(u'anchor', u'')
    path = reverse(viewname, *args, **kwargs) + anchor
    return complete_url(path, secure)
