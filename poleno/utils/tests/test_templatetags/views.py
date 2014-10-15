# vim: expandtab
# -*- coding: utf-8 -*-
from django.http import HttpResponse
from django.template import Context, Template

def active_view(request):
    return HttpResponse(Template(
        u'{% load active from poleno.utils %}'
        u'(index={{ request|active:"index" }})'
        u'(first={{ request|active:"first" }})'
        u'(second={{ request|active:"second" }})'
        u'(second:first={{ request|active:"second:first" }})'
    ).render(Context({
        u'request': request,
    })))

def language_view(request):
    return HttpResponse(Template(
        u'{% load change_lang from poleno.utils %}'
        u'({% change_lang "en" %})'
        u'({% change_lang "de" %})'
        u'({% change_lang "fr" %})'
    ).render(Context({
        u'request': request,
    })))
