# vim: expandtab
# -*- coding: utf-8 -*-
from django.shortcuts import render
from django.views.decorators.http import require_http_methods
from django.contrib.auth.decorators import login_required

@require_http_methods([u'HEAD', u'GET'])
@login_required
def profile(request):
    return render(request, u'accounts/profile.html')

