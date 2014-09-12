# vim: expandtab
# -*- coding: utf-8 -*-
from functools import wraps

from django.core.exceptions import PermissionDenied
from django.http import HttpResponseBadRequest
from django.utils.decorators import available_attrs
from django.contrib.auth.decorators import user_passes_test

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
            return HttpResponseBadRequest
        return view(request, *args, **kwargs)
    return wrapped_view

def login_required(view=None, **kwargs):
    u"""
    Decorator for views that checks that the user is logged in, redirecting to the log-in page if
    necessary. If ``raise_exception`` is True, ``PermissionDenied`` is rased instead of
    redirecting.

    Based on: django.contrib.auth.decorators.login_required

    Example:
        @login_required
        def view(request, ...):
            # We can assume now that the user is logged in. If he was not, he was redirected.

        @login_required(raise_exception=True)
        def view(request, ...):
            # We can assume now that the user is logged in. If he was not, he has got PermissionDenied.
    """
    raise_exception = kwargs.pop(u'raise_exception', False)
    def check(user):
        if user.is_authenticated():
            return True
        if raise_exception:
            raise PermissionDenied
        return False
    actual_decorator = user_passes_test(check, **kwargs)
    if view:
        return actual_decorator(view)
    return actual_decorator
