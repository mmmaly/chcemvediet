# vim: expandtab
# -*- coding: utf-8 -*-
from django.shortcuts import render
from django.http import JsonResponse
from django.template import RequestContext
from django.template.loader import render_to_string

def render_form(request, form, **context):
    return render(request, form.template, dict(context, form=form))

def json_form(request, form, **context):
    return JsonResponse({
            u'result': u'invalid',
            u'content': render_to_string(form.template, context_instance=RequestContext(request),
                dictionary=dict(context, form=form)),
            })

def json_draft():
    return JsonResponse({
            u'result': u'success',
            })

def json_success(request, inforequest, action=None, print_=False):
    return JsonResponse({
            u'result': u'success',
            u'scroll_to': u'#action-%d' % action.pk if action else None,
            u'content': render_to_string(u'inforequests/detail/detail.html', context_instance=RequestContext(request),
                dictionary=dict(inforequest=inforequest)),
            })
