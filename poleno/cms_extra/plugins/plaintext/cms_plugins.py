# vim: expandtab
from django.utils.translation import ugettext_lazy as _
from cms.plugin_pool import plugin_pool
from cms.plugin_base import CMSPluginBase

from models import PlainText

@plugin_pool.register_plugin
class PlainTextPlugin(CMSPluginBase):
    model = PlainText
    name = _("Plain Text")
    render_template = "cms/plugins/plaintext.html"

    def render(self, context, instance, placeholder):
        context.update({
            'placeholder': placeholder,
            'plugin': instance,
            'content': instance.content,
        })
        return context
