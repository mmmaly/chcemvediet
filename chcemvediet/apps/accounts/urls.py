# vim: expandtab
from django.conf.urls import patterns, url

import views

urlpatterns = patterns('',
    url(r'^profile/$', views.profile, name='profile'),
)

