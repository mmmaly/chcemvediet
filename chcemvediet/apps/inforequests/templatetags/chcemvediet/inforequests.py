# vim: expandtab
# -*- coding: utf-8 -*-
from collections import defaultdict

from django.forms.util import flatatt
from django.utils.safestring import mark_safe
from django.utils.html import format_html, format_html_join
from django.utils.dateformat import format

from poleno.utils.template import Library
from poleno.utils.misc import Bunch
from poleno.utils.html import format_html_tag

register = Library()

@register.simple_tag(takes_context=True)
def paper_field(context, field):
    attrs = {}
    if field.errors:
        attrs[u'class'] = u'with-tooltip tooltip-permanent tooltip-error'
        attrs[u'title'] = u' '.join(field.errors)

    if context.get(u'finalize'):
        value = field.form.cleaned_data[field.name]
        content = field.field.render_finalized(value)
    else:
        content = mark_safe(field.as_widget())

    return format_html(u'<span{0}>{1}</span>', flatatt(attrs), content)

@register.simple_pair_tag(takes_context=True)
def paragraph(content, context, before=1, after=1, editable=False, style=None):
    try:
        status = context[u'_paragraph_status']
    except KeyError:
        status = Bunch(opened=False, after=0)
        context[u'_paragraph_status'] = status
    html = []
    if status.opened and before > 0:
        html.append(format_html(u'</div>'))
        status.opened = False
    if not status.opened:
        spacing = max(before, status.after)
        attrs = defaultdict(list)
        if editable:
            attrs[u'class'].append(u'editable-container')
        if spacing > 1:
            attrs[u'style'].append(u'margin-top: {0}ex;'.format(spacing))
        if style:
            attrs[u'style'].append(style)
        html.append(format_html_tag(u'div', attrs))
        html.append(u'        ')
        status.opened = True
    html.append(format_html(u'{0}', content))
    if after > 0:
        html.append(format_html(u'</div>'))
        status.opened = False
    status.after = after
    html = format_html_join(u'', u'{0}', zip(html))
    return html

@register.simple_tag
def obligee_declension(obligee, declension, default=u''):
    if not obligee:
        return default
    if declension == u'nominative':
        return obligee.name
    return format_html(u'{0}<span style="color: red;">({1})</span>', obligee.name, declension)

@register.simple_tag
def obligee_gender(obligee, masculine, feminine, neuter, plural):
    if not obligee:
        return feminine
    return format_html(u'{0}<span style="color: red;">/{1}/{2}/{3}</span>', masculine, feminine, neuter, plural)
