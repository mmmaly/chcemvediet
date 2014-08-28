# vim: expandtab
# -*- coding: utf-8 -*-
import json

from django.http import HttpResponse
from django.template import  RequestContext
from django.template.loader import render_to_string

class JsonResponse(HttpResponse):
    u"""
    An HTTP response class that consumes data to be serialized to JSON.
    Borrowed from Django 1.7
    """
    def __init__(self, data, **kwargs):
        kwargs.setdefault(u'content_type', u'application/json')
        data = json.dumps(data)
        super(JsonResponse, self).__init__(content=data, **kwargs)

class Jdot(object):
    u"""
    JDOT = JSON DOM Transition
    """
    def __init__(self):
        self.list = []

    def as_response(self):
        return JsonResponse({u'jdot': self.list})

    def js(self, javascript, args=None):
        self.list.append({
            u'js': javascript,
            u'args': args,
            })
        return self

    def content_from_string(self, selector, html):
        self.js(ur"$(args.selector).html(args.html);", args={
                u'selector': selector,
                u'html': html,
            })
        return self

    def content(self, selector, request, template, context):
        self.content_from_string(selector, render_to_string(template, context, RequestContext(request)))
        return self

