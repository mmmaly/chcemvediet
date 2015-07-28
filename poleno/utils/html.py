# vim: expandtab
# -*- coding: utf-8 -*-
from django.utils.html import format_html, format_html_join

def merge_html_attrs(*args, **kwargs):
    u"""
    Merges html tag attributes from multiple dictionaries and keyword arguments. If multiple
    dictionaries define a "class" or a "style" attribute, all "class" and "style" attributes are
    combined. Classes are unified and styles are concatenated. If there is any other attribute in
    more than one dictionary, ``ValueError`` is raised.

    Example:
        >>> a = {'href': '#', 'title': 'Title'}
        >>> b = {'class': 'btn', 'style': 'color: red;'}
        >>> merge_html_attrs(a, b, alt='Go', class_='btn-go', style='border: 1px;')
        {'href': '#', 'title': 'Title', 'class': 'btn btn-go', style: 'color: red; border: 1px;', alt: 'Go'}

    """
    attrs = {}
    for arg in args + (kwargs,):
        if not arg:
            continue
        for key, val in arg.items():
            if key in [u'class', u'class_']:
                if not isinstance(val, list):
                    val = [val]
                for v in val:
                    attrs.setdefault(u'class', {}).update(dict.fromkeys(v.split()))
            elif key == u'style':
                if isinstance(val, list):
                    attrs.setdefault(u'style', []).extend(val)
                else:
                    attrs.setdefault(u'style', []).append(val)
            elif key in attrs:
                raise ValueError(u'Duplicate attribute "%s".' % key)
            else:
                attrs[key] = val
    if u'class' in attrs:
        attrs[u'class'] = u' '.join(attrs[u'class'].keys())
    if u'style' in attrs:
        attrs[u'style'] = u' '.join(attrs[u'style'])
    return attrs

def format_html_tag(tag, *args, **kwargs):
    closed = kwargs.pop(u'closed', False)
    attrs = merge_html_attrs(*args, **kwargs)
    attrs = format_html_join(u'', u' {0}="{1}"', attrs.items())
    html = format_html(u'<{0}{1}{2}>', tag, attrs, u' /' if closed else u'')
    return html
