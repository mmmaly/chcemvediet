# vim: expandtab
# -*- coding: utf-8 -*-
import json
from functools import wraps

from django.core.urlresolvers import reverse
from django.core.exceptions import ObjectDoesNotExist
from django.conf.urls import patterns, url
from django.db import models
from django.http import HttpResponse, HttpResponseNotFound
from django.utils.translation import ugettext_lazy as _
from django.utils.html import format_html, format_html_join, conditional_escape
from django.utils.decorators import available_attrs
from django.utils.safestring import mark_safe
from django.contrib import admin

from poleno.utils.html import format_tag

def extend_model_admin(model, mixin):
    klass = admin.site._registry[model].__class__

    class AugmentedModelAdmin(mixin, klass):
        pass

    admin.site.unregister(model)
    admin.site.register(model, AugmentedModelAdmin)

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

def admin_obj_format_join(sep, objs, format=u'{tag}', args_generator=None, kwargs_generator=None):
    if not objs:
        return u'--'
    if args_generator is None:
        args_generator = (() for o in objs)
    if kwargs_generator is None:
        kwargs_generator = ({} for o in objs)
    return format_html_join(sep, u'{0}', ([admin_obj_format(obj, format, *args, **kwargs)]
            for obj, args, kwargs in zip(objs, args_generator, kwargs_generator)))

def live_field(*fields):
    def decorator(method):
        @wraps(method, assigned=available_attrs(method))
        def wrapped_method(self, obj=None, get=None):
            assert (obj is None) + (get is None) == 1

            args = []
            vals = []
            for field in fields:
                try:
                    field_obj = self.model._meta.get_field_by_name(field)[0]
                except models.FieldDoesNotExist:
                    field_obj = None
                try:
                    if field_obj is None:
                        if get is None:
                            arg = None
                            val = u''
                        else:
                            arg = get[field]
                            val = str(arg)
                    elif isinstance(field_obj, models.ForeignKey):
                        if get is None:
                            arg = getattr(obj, field)
                            val = str(arg.pk)
                        else:
                            arg = field_obj.rel.to._default_manager.get(pk=get[field])
                            val = str(arg.pk)
                    elif isinstance(field_obj, models.ManyToManyField):
                        if get is None:
                            arg = getattr(obj, field).all()
                            val = u','.join(str(a.pk) for a in arg)
                        else:
                            arg = []
                            val = []
                            for pk in get[field].split(u','):
                                try:
                                    a = field_obj.rel.to._default_manager.get(pk=pk)
                                    v = str(a.pk)
                                except (ObjectDoesNotExist, ValueError):
                                    a = None
                                    v = u''
                                arg.append(a)
                                val.append(v)
                    else:
                        if get is None:
                            arg = getattr(obj, field)
                            val = str(arg)
                        else:
                            arg = get[field]
                            val = str(arg)
                except (ObjectDoesNotExist, KeyError, AttributeError, ValueError):
                    arg = None
                    val = u''
                args.append(arg)
                vals.append(val)
            res = method(self, *args)
            res = conditional_escape(res)
            res = mark_safe(res.replace(u'\n', u'<br/>'))

            info = self.model._meta.app_label, self.model._meta.model_name
            attrs = {
                    u'class': u'live-field',
                    u'data-fields': json.dumps(fields),
                    u'data-url': reverse(u'admin:%s_%s_live' % info, args=[method.__name__]),
                    }
            attrs.update({u'data-value-%s' % f: v for f, v in zip(fields, vals)})
            res = format_tag(u'span', attrs, res)
            return res
        return wrapped_method
    return decorator

class AdminLiveFieldsMixin(admin.ModelAdmin):

    def live_view(self, request, field):
        if field not in self.live_fields:
            return HttpResponseNotFound()
        res = getattr(self, field)(get=request.GET)
        return HttpResponse(res)

    def get_urls(self):
        info = self.model._meta.app_label, self.model._meta.model_name
        urls = patterns('',
                url(_(r'^live/(.+)/$'), self.admin_site.admin_view(self.live_view), name=u'%s_%s_live' % info),
                )
        return urls + super(AdminLiveFieldsMixin, self).get_urls()
