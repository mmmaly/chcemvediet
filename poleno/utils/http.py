# vim: expandtab
# -*- coding: utf-8 -*-
import os
import stat
from threading import local

from django.http import HttpResponseNotModified, FileResponse, JsonResponse
from django.utils.deprecation import MiddlewareMixin
from django.views.static import was_modified_since
from urllib.parse import quote as urlquote
from django.utils.http import http_date

# Thread local data
_local = local()

def get_request():
    return getattr(_local, u'request', None)

class RequestProviderMiddleware(MiddlewareMixin):

    def process_request(self, request):
        _local.request = request
        return None

    def process_response(self, request, response):
        _local.request = None
        return response


def send_file_response(request, path, name, content_type, attachment=True):
    # Based on: django.views.static.serve

    # FIXME: If running on real Apache server, we should use "X-SENDFILE" header to let Apache
    # serve the file. It's much faster. Possibly will be fixed in Django 1.8.
    # See: http://django.readthedocs.org/en/latest/ref/request-response.html#django.http.FileResponse

    statobj = os.stat(path)
    if not stat.S_ISREG(statobj.st_mode):
        raise OSError(u'Not a regular file: {}'.format(path))
    http_header = request.META.get(u'HTTP_IF_MODIFIED_SINCE')
    if not was_modified_since(http_header, statobj.st_mtime, statobj.st_size):
        return HttpResponseNotModified()
    response = FileResponse(open(path, u'rb'), content_type=content_type)
    response[u'Last-Modified'] = http_date(statobj.st_mtime)
    response[u'Content-Length'] = statobj.st_size
    if attachment:
        response[u'Content-Disposition'] = "attachment; filename*=UTF-8''{}".format(urlquote(name))
    return response


class JsonOperations(JsonResponse):
    def __init__(self, *args):
        super(JsonOperations, self).__init__({
            u'result': u'operations',
            u'operations': [a.to_dict() for a in args],
            })

class JsonOperation(object):
    def __init__(self, operation, **kwargs):
        self.operation = operation
        self.kwargs = kwargs
    def to_dict(self):
        return dict(operation=self.operation, **self.kwargs)

class JsonContent(JsonOperation):
    def __init__(self, target, content):
        super(JsonContent, self).__init__(u'content', target=target, content=content)

class JsonRedirect(JsonOperation):
    def __init__(self, location):
        super(JsonRedirect, self).__init__(u'redirect', location=location)

class JsonCloseModal(JsonOperation):
    def __init__(self):
        super(JsonCloseModal, self).__init__(u'close-modal')
