# vim: expandtab
from django.conf.urls import patterns, url

import views

urlpatterns = patterns('',
    url(r'^$', views.index_view, name='index'),
    url(r'^create/$', views.create_view, name='create'),
    url(r'^detail/(?P<application_id>\d+)/$', views.detail_view, name='detail'),
)

