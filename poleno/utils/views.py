# vim: expandtab
# -*- coding: utf-8 -*-
from functools import wraps

from django.core.exceptions import PermissionDenied
from django.http import HttpResponseBadRequest, HttpResponseRedirect
from django.conf import settings
from django.contrib.auth.decorators import user_passes_test
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

def secure_required(view=None, raise_exception=False):
    u"""
    Decorator for views that checks that the request is over HTTPS, redirecting if necessary. If
    ``raise_exception`` is True, ``PermissionDenied`` is rased instead of redirection. Note that
    the HTTPS check is disabled if DEBUG is true.

    Example:
        @secure_required
        def view(request, ...):
            # We can assume now the request is over HTTPS. If it was not, it was redirected.

        @secure_required(raise_exception=True)
        def view(request, ...):
            # We can assume now the request is over HTTPS. If it was not, PermissionDenied was
            # raised.
    """
    def actual_decorator(view):
        @wraps(view, assigned=available_attrs(view))
        def wrapped_view(request, *args, **kwargs):
            if settings.DEBUG or request.is_secure():
                return view(request, *args, **kwargs)
            if raise_exception:
                raise PermissionDenied
            request_url = request.build_absolute_uri(request.get_full_path())
            secure_url = request_url.replace(u'http://', u'https://', 1)
            return HttpResponseRedirect(secure_url)
        return wrapped_view
    if view:
        return actual_decorator(view)
    return actual_decorator
