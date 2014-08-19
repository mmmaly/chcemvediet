# vim: expandtab
from django.shortcuts import render
from django.views.decorators.http import require_http_methods

@require_http_methods(['HEAD', 'GET'])
def index(request):
    return render(request, 'main/pages/index.html')

@require_http_methods(['HEAD', 'GET'])
def about(request):
    return render(request, 'main/pages/about.html')

