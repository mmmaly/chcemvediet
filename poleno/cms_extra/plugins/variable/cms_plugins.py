# vim: expandtab
# -*- coding: utf-8 -*-
from django.utils.translation import ugettext_lazy as _
from django.utils.safestring import mark_safe
from django.template import Template
from django.template.context import Context
from django.conf import settings
from cms.plugin_pool import plugin_pool
from cms.plugin_base import CMSPluginBase

from models import Variable

@plugin_pool.register_plugin
class VariablePlugin(CMSPluginBase):
    model = Variable
    name = _("Variable")
    render_template = "cms/plugins/variable.html"
    text_enabled = True

    def render(self, context, instance, placeholder):
        try:
            t = Template(instance.content)
            content = t.render(Context(context))
        except Exception as e:
            content = str(e)

        context.update({
            'content': mark_safe(content),
            'placeholder': placeholder,
            'plugin': instance,
            })
        return context

    def icon_src(self, instance):
        return settings.STATIC_URL + 'cms/images/plugins/snippet.png'

    def icon_alt(self, instance):
        # Django-cms mangles '\', '"', "'", '<', '>', '&', '=', '-' and ';' characters in the
        # returned string. It's thanks to poorly used escapejs() when dealing with the returned
        # string. So we replace them with some fancy unicode characters that look similar.
        from django.utils.html import _js_escapes
        table = {k: u' ' for k in _js_escapes.keys()}
        table.update({
            ord(u'\\'): u'∖',
            ord(u"'"): u'❜',
            ord(u'"'): u'❞',
            ord(u'<'): u'',
            ord(u'>'): u'',
            ord(u'&'): u'',
            ord(u'='): u'',
            ord(u'-'): u'',
            ord(u';'): u'',
            })

        alt = instance.content.translate(table)
        return alt

