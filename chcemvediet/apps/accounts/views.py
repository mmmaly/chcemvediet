# vim: expandtab
from django.shortcuts import render
from django.views.decorators.http import require_http_methods
from django.contrib.auth.decorators import login_required

@login_required
@require_http_methods(['HEAD', 'GET'])
def profile(request):
    return render(request, 'accounts/profile.html')

