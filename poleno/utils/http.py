# vim: expandtab
# -*- coding: utf-8 -*-
import os
import json
import stat

from django.http import HttpResponse, HttpResponseNotModified, CompatibleStreamingHttpResponse
from django.views.static import was_modified_since
from django.template import  RequestContext
from django.template.loader import render_to_string
from django.utils.http import http_date, urlquote

class JsonResponse(HttpResponse):
    u"""
    An HTTP response class that consumes data to be serialized to JSON.
    Borrowed from Django 1.7
    """
    def __init__(self, data, **kwargs):
        kwargs.setdefault(u'content_type', u'application/json')
        data = json.dumps(data)
        super(JsonResponse, self).__init__(content=data, **kwargs)

def send_file_response(request, path, name, content_type):
    # Based on: django.views.static.serve

    # FIXME: If running on real Apache server, we should use "X-SENDFILE" header to let Apache
    # server the file. It's much faster.

    # FIXME: "Content-Disposition" filename is very fragile if contains non-ASCII characters.
    # Current implementation works on Firefox, but probably fails on other browsers. We should test
    # and fix it for them and/or sanitize and normalize file names.
    statobj = os.stat(path)
    if not stat.S_ISREG(statobj.st_mode):
        raise OSError(u'Not a regular file: %s' % path)
    if not was_modified_since(request.META.get(u'HTTP_IF_MODIFIED_SINCE'), statobj.st_mtime, statobj.st_size):
        return HttpResponseNotModified()
    response = CompatibleStreamingHttpResponse(open(path, u'rb'), content_type=content_type)
    response[u'Last-Modified'] = http_date(statobj.st_mtime)
    response[u'Content-Disposition'] = "attachment; filename*=UTF-8''%s" % urlquote(name)
    response[u'Content-Length'] = statobj.st_size
    return response
