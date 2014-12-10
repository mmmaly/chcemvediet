# vim: expandtab
# -*- coding: utf-8 -*-
import random
from functools import partial

from django.template import Library
from django.template.defaultfilters import stringfilter
from django.core.urlresolvers import resolve, reverse
from django.conf import settings
from django.contrib.webdesign.lorem_ipsum import paragraphs
from django.contrib.contenttypes.models import ContentType
from django.utils.html import format_html

from poleno.utils.misc import squeeze as squeeze_func
from poleno.utils.date import utc_date as utc_date_func, local_date as local_date_func
from poleno.utils.translation import translation

register = Library()

@register.filter
def subtract(value, arg):
    u"""
    Subtracting variables in Django templates.

    Example:
        {{ value|subtract:arg }}
    """
    return value - arg

@register.filter
def negate(value):
    u"""
    Negating (i.e. multiplying by -1) variable in Django templates.

    Example:
        {% if value > 0 %}
          add {{ value }}
        {% else %}
          substract {{ value|negate }}
        {% endif %}
    """
    return -value

@register.filter(name=u'range')
def range_(a, b):
    u"""
    Returns python range list.

    Usage format:

        "a"|range:"b"

    Examples:
      * ``"0"|range:"5"`` will return ``[0, 1, 2, 3, 4]``
      * ``"-3"|range:"4"`` will return ``[-3, -2, -1, 0, 1, 2, 3]``
      * ``"0"|range:"0"`` will return ``[]``
    """
    try:
        return range(int(a), int(b))
    except (ValueError, TypeError):
        return []

@register.filter
def utc_date(dt):
    u"""
    Converts aware ``datetime`` ``dt`` to UTC and returns its day as ``date``.

    Example:
        {{ dt|utc_date }}
    """
    return utc_date_func(dt)

@register.filter
def local_date(dt, tz=None):
    u"""
    Converts aware ``datetime`` ``dt`` to timezone ``tz``, by default the current time zone, and
    returns its day as ``date``.

    Example:
        {{ dt|local_date }}
        {{ dt|local_date:tz }}
    """
    return local_date_func(dt, tz=tz)

@register.filter
def active(request, view_prefix):
    u"""
    Tests if the active view name has prefix ``view_prefix``. View name is colon separated list of
    view namespaces and the actual url name. Thus if the active view is 'namespace:name', then the
    function returns ``True`` for 'namespace' and 'namespace:name', but not for 'name' or
    'namespace:other'.
    """
    # FIXME: Should probably be {% ifactive arg %}...{% endif %} tag. Filter doesn't make much
    # sense here.
    try:
        resolved = resolve(request.path)
    except Exception: # pragma: no cover
        return False
    if not (resolved.view_name + u':').startswith(view_prefix + u':'):
        return False
    return True

@register.filter(is_safe=True)
@stringfilter
def squeeze(text):
    u"""
    Substitutes all whitespace including new lines with single spaces, striping any leading or
    trailing whitespace. Beware that the filter does not treat HTML tags specially and it will
    replace all whitespace in them as well.

    Example:
        "   text   with\nspaces\n\n" -> "text with spaces"

    Example:
        {% filter squeeze %}
          Long text you want
          to squeeze
        {% endfilter %}
    """
    return squeeze_func(text)

@register.filter
def generic_type(value):
    u"""
    Returns ``ContentType`` object for given model class or model instance.

    Example:
        {{ request.user|generic_type|method:"pk" }} prints pk of user ContentType object.
    """
    return ContentType.objects.get_for_model(value)

@register.filter
def method(value, arg):
    u"""
    Tool to call object methods in templates.
    Source: https://djangosnippets.org/snippets/424/

    Example:
        class Foo:
            def bar(self, a, b, c):
                pass
            def bop(self, a):
                pass

        In template with { "foo": Foo() } passed as context:
            {{ foo|method:"bar"|with:"one"|with:"two"|with:"three"|call }}
            {{ foo|method:"bop"|call_with:"baz" }}
    """
    try:
        return value[arg]
    except (TypeError, KeyError, IndexError):
        pass
    try:
        return getattr(value, str(arg))
    except AttributeError:
        pass
    return u'[no method %s]' % arg

@register.filter
def call_with(value, arg):
    u""" See ``method`` """
    if not callable(value):
        return '[not callable]'
    return value(arg)

@register.filter
def call(value):
    u""" See ``method`` """
    if not callable(value):
        return u'[not callable]'
    return value()

@register.filter(name="with")
def with_(value, arg):
    u""" See ``method`` """
    if not callable(value):
        return u'[not callable]'
    return partial(value, arg)

@register.simple_tag
def lorem(randseed=None, count=1, method=None):
    u"""
    Creates Lorem Ipsum text.

    Usage format:

        {% lorem [randseed] [count] [method] %}

    ``randseed`` is any hashable object used to initialize the random numbers generator.
    If ``randseed`` is not given the common "Lorem ipsum dolor sit..." text is used.

    ``count`` is a number of paragraphs or sentences to generate (default is 1).

    ``method`` is either ``p`` for HTML paragraphs enclosed in ``<p>`` tags, or ``b`` for
    plain-text paragraph blocks (default is ``b``).

    Notice: This filter is rewrited ``lorem`` filter from ``webdesign`` modul from default Django
    package ``django.contrib.webdesign``. The original ``lorem`` filter does not give stable random
    text, thus its generated paragraphs change on every page refresh. We stabilize the generated
    text by setting a fixed randseed before generating the paragraph.
    """

    state = random.getstate()
    random.seed(randseed)
    res = paragraphs(count, common=(randseed is None))
    random.setstate(state)

    if method == u'p':
        res = [u'<p>%s</p>' % p for p in res]
    return u'\n'.join(res)

@register.simple_tag(takes_context=True)
def change_lang(context, lang=None):
    u"""
    Get active page's url with laguage changed to the specified language.

    Example:
        {% change_lang 'en' %}

    Source: https://djangosnippets.org/snippets/2875/
    """
    path = context[u'request'].path
    url_parts = resolve(path)

    with translation(lang):
        url = reverse(url_parts.view_name, kwargs=url_parts.kwargs)

    return u'%s' % url

@register.simple_tag
def external_css():
    u"""
    Render links to external css styles. Uses settins.EXTERNAL_CSS to get their list.
    """
    return u'\n'.join(format_html(u'<link href="{0}" rel="stylesheet">', url) for url in settings.EXTERNAL_CSS)

@register.simple_tag
def external_js():
    u"""
    Render links to external javascript. Uses settins.EXTERNAL_JS to get their list.
    """
    return u'\n'.join(format_html(u'<script src="{0}"></script>', url) for url in settings.EXTERNAL_JS)
