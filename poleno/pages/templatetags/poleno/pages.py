# vim: expandtab
# -*- coding: utf-8 -*-
import os

from django.core.urlresolvers import reverse, resolve
from django.template import Library
from django.utils.translation import get_language

from poleno.utils.translation import translation
from poleno.pages.pages import File, Page

register = Library()

@register.simple_tag(takes_context=True)
def page(context, *args):
    u"""
    Get page url. The page may be given with an absolute path or with a relative path
    with respect to the current page. If there is no current page, only absolute path
    may be given. The returned page is always is the same language as the current page.
    If you want to speficy different page paths for different languages, use multiple
    arguments prefixed with particular language code.

    Example: (Assuming the current page is '/sk/test/')
       Absolute path:
           {% page "/moo/foo/" %}                       -> /sk/moo/foo/
           {% page "/" %}                               -> /sk/
       Ralative path:
           {% page "foo/goo/" %}                        -> /sk/test/foo/goo/
           {% page "../" %}                             -> /sk/
           {% page "../foo/goo/" %}                     -> /sk/foo/goo/
           {% page "../../../../foo/goo/" %}            -> /sk/foo/goo/
       Path with no trailing slash:
           {% page "/moo/foo" %}                        -> /sk/foo/goo/
           {% page "foo/goo" %}                         -> /sk/test/foo/goo/
       File path:
           {% page "moo.jpg" %}                         -> /sk/test/moo.jpg
           {% page "/moo/foo/moo.jpg" %}                -> /sk/moo/foo/moo.jpg
           {% page "foo/goo/moo.jpg" %}                 -> /sk/test/foo/goo/moo.jpg
       Language alternatives:
           {% page "en:moo/enfoo" "sk:moo/skfoo" %}     -> /sk/test/moo/skfoo/
           {% page "en:moo/enfoo" "moo/xxfoo" %}        -> /sk/test/moo/xxfoo/
           {% page "en:moo/enfoo" %}                    -> /sk/test/
    """
    try:
        page = context[u'page']
        lang = page.lang
        path = page.path
    except (KeyError, AttributeError):
        lang = get_language()
        path = u'/'

    for arg in args:
        if u':' in arg:
            prefix, arg = arg.split(u':', 1)
            if prefix != lang:
                continue
        path = os.path.normpath(os.path.join(path, arg))
        break

    ppath, name = path.rsplit(u'/', 1)
    if u'.' in name:
        if not ppath.endswith(u'/'):
            ppath += u'/'
        return reverse(u'pages:file', args=[ppath.lstrip(u'/'), name])
    else:
        if not path.endswith(u'/'):
            path += u'/'
        return reverse(u'pages:view', args=[path.lstrip(u'/')])

@register.filter
def page_active(request, path):
    try:
        resolved = resolve(request.path)
    except Exception as e:
        return False
    if resolved.view_name != u'pages:view':
        return False
    if not resolved.kwargs.get(u'path', u'').startswith(path.lstrip(u'/')):
        return False
    return True

@register.assignment_tag(takes_context=True)
def get_page(context, *args):
    try:
        page = context[u'page']
        lang = page.lang
        path = page.path
    except (KeyError, AttributeError):
        lang = get_language()
        path = u'/'

    for arg in args:
        if u':' in arg:
            prefix, arg = arg.split(u':', 1)
            if prefix != lang:
                continue
        path = os.path.normpath(os.path.join(path, arg))
        break

    ppath, name = path.rsplit(u'/', 1)
    if u'.' in name:
        return File(Page(ppath, lang), name)
    else:
        return Page(path, lang)
