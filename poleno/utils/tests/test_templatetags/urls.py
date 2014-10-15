# vim: expandtab
# -*- coding: utf-8 -*-
from django.conf.urls import patterns, url, include
from django.conf.urls.i18n import i18n_patterns

from poleno.utils.tests.test_templatetags import views, urls_second

urlpatterns = patterns(u'',
    url(r'^$', views.active_view, name=u'index'),
    url(r'^first/', views.active_view, name=u'first'),
    url(r'^second/', include(urls_second, namespace=u'second')),
)

urlpatterns += i18n_patterns(u'',
    url(r'^language/', views.language_view, name=u'language'),
)
