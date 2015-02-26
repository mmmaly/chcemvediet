# vim: expandtab
# -*- coding: utf-8 -*-

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
                attrs.setdefault(u'class', {}).update(dict.fromkeys(val.split()))
            elif key == u'style':
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
