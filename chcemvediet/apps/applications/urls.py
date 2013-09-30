# vim: expandtab
from django.conf.urls import patterns, url

import views

urlpatterns = patterns('',
    url(r'^$', views.index, name='index'),
    url(r'^create/$', views.create, name='create'),
    url(r'^detail/(?P<application_id>\d+)/$', views.detail, name='detail'),
)

