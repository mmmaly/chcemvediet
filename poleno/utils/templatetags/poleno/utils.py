# vim: expandtab
# -*- coding: utf-8 -*-
import re
import random
from functools import partial

from django.template.defaultfilters import stringfilter
from django.core.urlresolvers import resolve, Resolver404
from django.conf import settings
from poleno.utils.lorem_ipsum import paragraphs
from django.contrib.contenttypes.models import ContentType
from django.contrib.staticfiles.storage import staticfiles_storage
from django.utils.html import format_html
from django.utils.safestring import mark_safe

from poleno.utils.urls import reverse, complete_url
from poleno.utils.misc import squeeze as squeeze_func
from poleno.utils.date import utc_date as utc_date_func, local_date as local_date_func
from poleno.utils.translation import translation
from poleno.utils.template import Library


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
def times(value, arg):
    u"""
    Multiple variables in Django templates.

    Example:
        {{ value|times:arg }}
        {{ "xxx"|times:10 }}
    """
    return value * arg

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

@register.filter(name=u'min')
def min_(value, arg):
    return min(value, arg)

@register.filter(name=u'max')
def max_(value, arg):
    return max(value, arg)

@register.filter
def yes(value, arg):
    if value:
        return arg
    else:
        return u''

@register.filter
def no(value, arg):
    if value:
        return u''
    else:
        return arg

@register.filter
def eq(value, arg):
    return value == arg

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
def active(request, view_prefixes):
    u"""
    Tests if the active view name has any of comma separated prefix ``view_prefixes``. View name is
    colon separated list of view namespaces and the actual url name. Thus if the active view is
    'namespace:name', then the function returns ``True`` for 'namespace' and 'namespace:name', but
    not for 'name' or 'namespace:other'.
    """
    try:
        resolved = resolve(request.path)
    except Exception: # pragma: no cover
        return False
    for view_prefix in view_prefixes.split(u','):
        if (resolved.view_name + u':').startswith(view_prefix + u':'):
            return True
    return False

@register.filter
def completeurl(path, secure=False):
    if path:
        return complete_url(path, secure)
    else:
        return u''

@register.filter
def adminurl(obj, view=u'change'):
    try:
        view_name = u'admin:{}_{}_{}'.format(obj._meta.app_label, obj._meta.model_name, view)
        return reverse(view_name, args=[obj.pk])
    except:
        return u''

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
def split(value, separator=None):
    return value.split(separator)

@register.filter
def generic_type(value):
    u"""
    Returns ``ContentType`` object for given model class or model instance.

    Example:
        {{ request.user|generic_type|method:"pk" }} prints pk of user ContentType object.
    """
    return ContentType.objects.get_for_model(value)

@register.filter(name=u'getattr')
def getattr_(value, arg):
    return getattr(value, arg)

@register.filter
def getkey(value, key):
    return value.get(key)

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
    return u'[no method {}]'.format(arg)

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

@register.filter(name=u'with')
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
        res = [u'<p>{}</p>'.format(p) for p in res]
        return mark_safe(u'\n'.join(res))
    return u'\n'.join(res)

@register.simple_tag
def plural(value, *args):
    u"""
    Return plural variant of text.

    Usage format:

        {% plural <value> "cond:text" ... %}

    where ``value`` is a number, ``text`` is any string and ``cond`` is a comma separated list of
    terms. Every term is an empty string, a single integer or an interval. Intervals are specified by
    their lower and upper bounds separated by "~". The bounds are inclusive and may be any positive
    or negative integer. Any of the bounds may be omitted. Omitted bounds mean infinity.

    The text may contain "{n}" to format the value.

    Examples:
        {% plural n "1:jablko" "2~4:jablká" "jabĺk" %}
        {% plural n "-1,1:jablko" "-4~-2,2~4:jablká" "jabĺk" %}
        {% plural n "1:bol {n} strom" "2~4:boli {n} stromy" "bolo {n} stromov" %}
    """
    value = int(value)
    for arg in args:
        if u':' in arg:
            cond, res = arg.split(u':', 1)
        else:
            cond, res = u'', arg
        for term in cond.split(u','):
            if u'~' in term:
                a, b = term.split(u'~', 1)
            else:
                a, b = term, term
            if (a == u'' or int(a) <= value) and (b == u'' or value <= int(b)):
                return res.format(n=value)
    return u''

@register.simple_tag(takes_context=True)
def assign(context, **kwargs):
    for key, val in kwargs.items():
        context[key] = val
    return u''

@register.simple_pair_tag(takes_context=True)
def capture(content, context, variable):
    context[variable] = content
    return u''

@register.simple_tag(takes_context=True)
def change_lang(context, lang=None):
    u"""
    Get active page's url with language changed to the specified language.

    Example:
        {% change_lang 'en' %}

    Source: https://djangosnippets.org/snippets/2875/
    """
    path = context[u'request'].path
    try:
        url_parts = resolve(path)
        view_name = url_parts.view_name
        args = url_parts.args
        kwargs = url_parts.kwargs

        # Ask the view what to show after changing language.
        if hasattr(url_parts.func, u'change_lang'):
            view_name, args, kwargs = url_parts.func.change_lang(lang, *args, **kwargs)

        with translation(lang):
            url = reverse(view_name, args=args, kwargs=kwargs)
    except Resolver404:
        url = path

    query = context[u'request'].GET.urlencode()
    url = url + u'?' + query if query else url
    return format(url)

@register.simple_tag
def url(viewname, *args, **kwargs):
    return reverse(viewname, args=args, kwargs=kwargs)

ASSETS_TYPES = { # {{{
        u'js': (
            re.compile(r'[./]js([?#]|$)'),
            u'<script src="{url}" type="text/javascript" charset="utf-8"></script>',
            ),
        u'css': (
            re.compile(r'[./]css([?#]|$)'),
            u'<link href="{url}" rel="stylesheet" type="text/css" charset="utf-8">',
            ),
        u'scss': (
            re.compile(r'[.]s[ac]ss$'),
            u'<link href="{url}" rel="stylesheet" type="text/x-scss">',
            ),
        } # }}}

@register.simple_tag
def assets(types, external=False, local=False):
    u"""
    Render links to local and external assets defined in settings.ASSETS.

    Example:
        {% assets "js" external=True %}
        {% assets "css,scss" local=True %}
    """
    res = []
    types = types.split(u',')
    for asset in settings.ASSETS:
        # Only local/external assets
        if asset.startswith(u'//'):
            if not external:
                continue
            url = asset
        else:
            if not local:
                continue
            url = staticfiles_storage.url(asset)
        # Only given types
        for type in types:
            type_re, type_tpl = ASSETS_TYPES[type]
            if type_re.search(url):
                res.append(format_html(type_tpl, url=url))
                break
    return u'\n'.join(res)
