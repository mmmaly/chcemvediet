# vim: expandtab
from django.conf.urls import patterns, url

import views

urlpatterns = patterns(u'',
    url(r'^$', views.index, name=u'index'),
    url(r'^autocomplete/$', views.autocomplete, name=u'autocomplete'),
)

