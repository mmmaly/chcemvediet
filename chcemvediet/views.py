# vim: expandtab
from django.shortcuts import render

def index(request):
    return render(request, 'main/pages/index.html')

def about(request):
    return render(request, 'main/pages/about.html')

