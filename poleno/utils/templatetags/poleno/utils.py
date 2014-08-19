# vim: expandtab
import random

from django import template
from django.core.urlresolvers import resolve, reverse
from django.utils.translation import activate, get_language
from django.contrib.webdesign.lorem_ipsum import paragraphs


register = template.Library()

@register.filter(name='range')
def range_(a, b):
    """
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
def active(request, view_prefix):
    """
    Tests if the active view name has prefix ``view_prefix``. View name is colon separated list of
    view namespaces and the actual url name. Thus if the active view is 'namespace:name', then the
    function returns ``True`` for 'namespace' and 'namespace:name', but not for 'name' or
    'namespace:other'.
    """
    try:
        resolved = resolve(request.path)
    except:
        return False
    if not (resolved.view_name + ':').startswith(view_prefix + ':'):
        return False
    return True

@register.simple_tag
def lorem(randseed=None, count=1, method=None):
    """
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

    if method == 'p':
        res = ['<p>%s</p>' % p for p in res]
    return '\n'.join(res)

@register.simple_tag(takes_context=True)
def change_lang(context, lang=None):
    """
    Get active page's url by a specified language
    Usage: {% change_lang 'en' %}

    Source: https://djangosnippets.org/snippets/2875/
    """

    path = context['request'].path
    url_parts = resolve(path)

    url = path
    cur_language = get_language()
    try:
        activate(lang)
        url = reverse(url_parts.view_name, kwargs=url_parts.kwargs)
    finally:
        activate(cur_language)

    return '%s' % url
