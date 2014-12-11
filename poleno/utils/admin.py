# vim: expandtab
# -*- coding: utf-8 -*-
from django.core.urlresolvers import reverse
from django.utils.html import format_html
from django.contrib import admin

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

def admin_obj_format(obj, format=u'{tag}', *args, **kwargs):
    link = kwargs.pop(u'link', True)
    if obj is None:
        return u'--'
    tag = u'<%s: %s>' % (obj.__class__.__name__, obj.pk)
    res = format.format(obj=obj, tag=tag, *args, **kwargs)
    if link:
        info = obj._meta.app_label, obj._meta.module_name
        url = reverse(u'admin:%s_%s_change' % info, args=[obj.pk])
        res = format_html(u'<a href="{0}">{1}</a>', url, res)
    return res

def extend_model_admin(model, mixin):
    klass = admin.site._registry[model].__class__

    class AugmentedModelAdmin(mixin, klass):
        pass

    admin.site.unregister(model)
    admin.site.register(model, AugmentedModelAdmin)
