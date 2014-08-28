# vim: expandtab
# -*- coding: utf-8 -*-
from functools import wraps

from django.http import HttpResponseBadRequest
from django.utils.decorators import available_attrs

def require_ajax(view):
    u"""
    Decorator to make a view only accept AJAX requests

    Example:
        @require_ajax
        def view(request, ...):
            # We can assume now that only AJAX request gets here
    """
    @wraps(view, assigned=available_attrs(view))
    def wrapped_view(request, *args, **kwargs):
        if not request.is_ajax():
            return HttpResponseBadRequest()
        return view(request, *args, **kwargs)
    return wrapped_view
