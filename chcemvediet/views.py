# vim: expandtab
# -*- coding: utf-8 -*-
from django.shortcuts import render
from django.views.decorators.http import require_http_methods

@require_http_methods([u'HEAD', u'GET'])
def index(request):
    return render(request, u'main/pages/index.html')

@require_http_methods([u'HEAD', u'GET'])
def about(request):
    return render(request, u'main/pages/about.html')

