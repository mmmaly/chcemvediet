# vim: expandtab
# -*- coding: utf-8 -*-
from django.conf.urls import patterns, url

from poleno.utils.tests.test_views import views

urlpatterns = patterns(u'',
    url(r'^require-ajax/$', views.require_ajax_view),
    url(r'^login-required-with-redirect/$', views.login_required_with_redirect_view),
    url(r'^login-required-with-exception/$', views.login_required_with_exception_view),
    url(r'^secure-required-with-redirect/$', views.secure_required_with_redirect_view),
    url(r'^secure-required-with-exception/$', views.secure_required_with_exception_view),
)
