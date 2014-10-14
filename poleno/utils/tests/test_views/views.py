# vim: expandtab
# -*- coding: utf-8 -*-
from django.http import HttpResponse
from poleno.utils.views import require_ajax, login_required, secure_required

@require_ajax
def require_ajax_view(request):
    return HttpResponse()

@login_required
def login_required_with_redirect_view(request):
    return HttpResponse()

@login_required(raise_exception=True)
def login_required_with_exception_view(request):
    return HttpResponse()

@secure_required
def secure_required_with_redirect_view(request):
    return HttpResponse()

@secure_required(raise_exception=True)
def secure_required_with_exception_view(request):
    return HttpResponse()
