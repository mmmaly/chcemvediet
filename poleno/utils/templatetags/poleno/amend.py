# vim: expandtab
# -*- coding: utf-8 -*-
import lxml.html

from poleno.utils.template import Library

register = Library()


def _flatten_parts(parent):
    parts = [parent.text or u'']
    for child in parent:
        parts.append(child)
        parts.append(child.tail or u'')
    return parts

def _combine_parts(parent, parts):
    parent.text = u''
    parent[:] = []
    for part in parts:
        if isinstance(part, str):
            try:
                parent[-1].tail += part
            except IndexError:
                parent.text += part
        else:
            part.tail = u''
            parent.append(part)
    return parent


@register.simple_pair_tag(takes_context=True, lazy_content=True)
def amend(content, context):
    u"""
    Edit a snippet of HTML by parsing it, manipulating its element tree and exporting it back to
    string. Usefull to make changes in opaque template snippets from external libraries.

    Example:
        {% amend %}
          {% include "template.html" %}
          {% prepend path=".//form" %}<p>Added paragraph</p>{% endprepend %}
        {% endamend %}

        Adds a paragraph at the beginning of each form in `template.html`.
    """
    with context.push():
        context[u'_amend'] = []

        fragment = lxml.html.fragment_fromstring(content(context), create_parent=u'root')
        for action in context[u'_amend']:
            fragment = action(fragment)

        return lxml.html.tostring(fragment)[6:-7] # Strip root tag

@register.simple_pair_tag(takes_context=True)
def prepend(content, context, path):
    u"""
    Select elements specified by XPath and insert `content` as child elements at the beginning of
    each of them. If the element begins with a text, the content in inserted before the text.

    Example:
        {% amend %}
          <ul>
            <li>aaa</li>
            <li>bbb</li>
          </ul>
          {% prepend path=".//ul" %}<li>xxx</li>{% endprepend %}
        {% endamend %}

    Result:
        <ul>
          <li>xxx</li>
          <li>aaa</li>
          <li>bbb</li>
        </ul>
    """
    def action(fragment):
        elements = fragment.findall(path)
        for element in elements:
            subtree = lxml.html.fragment_fromstring(content, create_parent=u'root')
            element_parts = _flatten_parts(element)
            subtree_parts = _flatten_parts(subtree)
            _combine_parts(element, subtree_parts + element_parts)
        return fragment

    if u'_amend' in context:
        context[u'_amend'].append(action)
    return u''

@register.simple_pair_tag(takes_context=True)
def append(content, context, path):
    u"""
    Select elements specified by XPath and insert `content` as child elements at the eand of each of
    them. If the element ends with a text, the content in inserted after the text.

    Example:
        {% amend %}
          <ul>
            <li>aaa</li>
            <li>bbb</li>
          </ul>
          {% append path=".//ul" %}<li>xxx</li>{% endappend %}
        {% endamend %}

    Result:
        <ul>
          <li>aaa</li>
          <li>bbb</li>
          <li>xxx</li>
        </ul>
    """
    def action(fragment):
        elements = fragment.findall(path)
        for element in elements:
            subtree = lxml.html.fragment_fromstring(content, create_parent=u'root')
            element_parts = _flatten_parts(element)
            subtree_parts = _flatten_parts(subtree)
            _combine_parts(element, element_parts + subtree_parts)
        return fragment

    if u'_amend' in context:
        context[u'_amend'].append(action)
    return u''

@register.simple_pair_tag(takes_context=True)
def before(content, context, path):
    u"""
    Select elements specified by XPath and insert `content` as sibling elements before each of them.
    If the element has a text before it, the content in inserted between the text and the element.

    Example:
        {% amend %}
          <ul>
            <li>aaa</li>
            <li>bbb</li>
            <li>ccc</li>
          </ul>
          {% before path=".//li[2]" %}<li>xxx</li>{% endbefore %}
        {% endamend %}

    Result:
        <ul>
          <li>aaa</li>
          <li>xxx</li>
          <li>bbb</li>
          <li>ccc</li>
        </ul>
    """
    def action(fragment):
        elements = fragment.findall(path)
        for element in elements:
            subtree = lxml.html.fragment_fromstring(content, create_parent=u'root')
            parent = element.getparent()
            index = parent.index(element)
            parent_parts = _flatten_parts(parent)
            subtree_parts = _flatten_parts(subtree)
            _combine_parts(parent,
                    parent_parts[0:2*index+1] + subtree_parts + parent_parts[2*index+1:])
        return fragment

    if u'_amend' in context:
        context[u'_amend'].append(action)
    return u''

@register.simple_pair_tag(takes_context=True)
def after(content, context, path):
    u"""
    Select elements specified by XPath and insert `content` as sibling elements after each of them.
    If the element has a text after it, the content in inserted between the element and the text.

    Example:
        {% amend %}
          <ul>
            <li>aaa</li>
            <li>bbb</li>
            <li>ccc</li>
          </ul>
          {% after path=".//li[2]" %}<li>xxx</li>{% endafter %}
        {% endamend %}

    Result:
        <ul>
          <li>aaa</li>
          <li>bbb</li>
          <li>xxx</li>
          <li>ccc</li>
        </ul>
    """
    def action(fragment):
        elements = fragment.findall(path)
        for element in elements:
            subtree = lxml.html.fragment_fromstring(content, create_parent=u'root')
            parent = element.getparent()
            index = parent.index(element)
            parent_parts = _flatten_parts(parent)
            subtree_parts = _flatten_parts(subtree)
            _combine_parts(parent,
                    parent_parts[0:2*index+2] + subtree_parts + parent_parts[2*index+2:])
        return fragment

    if u'_amend' in context:
        context[u'_amend'].append(action)
    return u''

@register.simple_tag(takes_context=True)
def delete(context, path):
    u"""
    Select elements specified by XPath and delete them together with their child elements. Any texts
    before and after deleted elements is preserved.

    Example:
        {% amend %}
          <ul>
            <li>aaa</li>
            <li>bbb</li>
            <li>ccc</li>
          </ul>
          {% delete path=".//li[2]" %}
        {% endamend %}

    Result:
        <ul>
          <li>aaa</li>
          <li>ccc</li>
        </ul>
    """
    def action(fragment):
        elements = fragment.findall(path)
        for element in elements:
            element.drop_tree()
        return fragment

    if u'_amend' in context:
        context[u'_amend'].append(action)
    return u''

@register.simple_tag(takes_context=True)
def set_attributes(context, path, **kwargs):
    u"""
    Select elements specified by XPath and add, remove or edit their attributes.

    Example:
        {% amend %}
          <ul>
            <li aaa="foo">xxx</li>
            <li aaa="foo">xxx</li>
            <li aaa="foo">xxx</li>
            <li aaa="foo">xxx</li>
            <li aaa="foo">xxx</li>
          </ul>
          {% set_attributes path=".//li[1]" aaa=None bbb=None %}
          {% set_attributes path=".//li[2]" aaa=False bbb=False %}
          {% set_attributes path=".//li[3]" aaa=True bbb=True %}
          {% set_attributes path=".//li[4]" aaa="bar" bbb="baz" ccc="" %}
          {% set_attributes path=".//li[5]" aaa=1 bbb=2 ccc=0 %}
        {% endamend %}

    Result:
        <ul>
          <li>xxx</li>
          <li>xxx</li>
          <li aaa bbb>xxx</li>
          <li aaa="bar" bbb="baz" ccc="">xxx</li>
          <li aaa="1" bbb="2" ccc="0">xxx</li>
        </ul>
    """
    def action(fragment):
        elements = fragment.findall(path)
        for element in elements:
            for key, value in kwargs.items():
                if value is None or value is False:
                    element.attrib.pop(key, None)
                elif value is True:
                    element.set(key, None)
                else:
                    element.set(key, str(value))
        return fragment

    if u'_amend' in context:
        context[u'_amend'].append(action)
    return u''
