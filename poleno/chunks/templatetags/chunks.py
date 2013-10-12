# vim: expandtab
# -*- coding: utf-8 -*-
from copy import copy

from django import template
from django.core.exceptions import ObjectDoesNotExist, MultipleObjectsReturned
from django.utils.html import escape
from django.template.defaultfilters import safe
from django.utils.translation import ugettext_lazy as _
from classytags.arguments import Argument, Flag
from classytags.core import Tag, Options

from .. import models

register = template.Library()

@register.tag
class Chunk(Tag):
    """
    Renders Chunk content.

    Usage format:

        {% chunk <id> [fragile] [width <width>] [language <language>] %}

    ``fragile`` marks that the Chunk is rendered in a fragile context. If the Chunk is rendered in
    a fragile context, the Chunk may not be rendered in edit mode. For instance, if the Chunk is
    placed betweed <title>...</title> html tags, it should be marked as fragile. Otherwise, we
    would get some gibberish edit mode tags in the title instead of the actual page title.

    ``id`` is the ``reverse_id`` identifier of the Chunk instance to render. If there is no Chunk
    with given identifier, an error message is rendered.

    ``width`` is the width argument for plugins included in the Chunk. The argument is optional and
    applies only to plugins that support it.

    ``language`` specifies the language in which the Chunk should be rendered. If omitted, current
    language is used.
    """
    options = Options(
        Argument('reverse_id'),
        Flag('fragile', true_values=('fragile',), default=False),
        'width',
        Argument('width', default=None, required=False),
        'language',
        Argument('language', default=None, required=False),
    )

    def render_tag(self, context, reverse_id, fragile, width, language):
        try:
            chunk = models.Chunk.objects.get(reverse_id=reverse_id)
        except ObjectDoesNotExist:
            return safe(_('Chunk "%(id)s" not found.') % {'id': escape(reverse_id)})
        except MultipleObjectsReturned:
            return safe(_('Chunk "%(id)s" identifier conflict.') % {'id': escape(reverse_id)})

        if fragile:
            # The chunk is fragile, so we want to skip admin edit mode for it. However, I have not
            # found any elegant way to render the Placeholder with its edit mode turned off. So,
            # temporarily we modify ``request.GET`` dictionary and remove ``edit`` argument from
            # it. After rendering the Placeholder, we restore ``request.GET`` to its original
            # value.
            request = context['request']
            original_get = request.GET
            try:
                request.GET = copy(original_get)
                request.GET.pop('edit', None)
                content = self._render_chunk(chunk, context, width, language)
            finally:
                # Restore ``request.GET`` to its original value.
                request.GET = original_get
        else:
            content = self._render_chunk(chunk, context, width, language)

        return content

    def _render_chunk(self, chunk, context, width, language):
        # Hack to display Chunk description in Placeholder toolbar. It should have been done
        # somewhere in Placeholder templates, but I don't know where and how. So I just create an
        # extra <div> with Chunk description and position it over Placeholder toolbar.
        content = ''
        request = context['request']
        toolbar = getattr(request, 'toolbar', None)
        if getattr(toolbar, 'edit_mode', False):
            text = escape(chunk.reverse_id+u' '+chunk.description)
            content += safe('<div class="cms_reset" style="position: relative;"><p style="position: absolute; left: 100px; top: 8px;">'+text+'</div></p>')

        content += safe(chunk.content.render(context, width, lang=language))
        return content
