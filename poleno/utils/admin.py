# vim: expandtab
# -*- coding: utf-8 -*-
from django.core.urlresolvers import reverse
from django.contrib import admin

from django.utils.html import escape

# FIXME: doc + tests
def simple_list_filter_factory(filter_title, filter_parameter_name, filters):
    class SimpleListFilter(admin.SimpleListFilter):
        title = filter_title
        parameter_name = filter_parameter_name

        def lookups(self, request, model_admin):
            for value, label, func in filters:
                yield (value, label)

        def queryset(self, request, queryset):
            for value, label, func in filters:
                if self.value() == value:
                    return func(queryset)

    return SimpleListFilter

# FIXME: doc + tests
def admin_obj_link(obj, text=u'', show_pk=False, link=True):
    if not text or show_pk:
        text = u'<%s: %s>%s' % (obj.__class__.__name__, obj.pk, text)
    html = escape(text)
    if link:
        url = reverse(u'admin:%s_%s_change' % (obj._meta.app_label, obj._meta.module_name), args=[obj.pk])
        html = u'<a href="%s">%s</a>' % (escape(url), html)
    return html

# FIXME: doc + tests
def extend_model_admin(model, mixin):
    klass = admin.site._registry[model].__class__

    class AugmentedModelAdmin(mixin, klass):
        pass

    admin.site.unregister(model)
    admin.site.register(model, AugmentedModelAdmin)
