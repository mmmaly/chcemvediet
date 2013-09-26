# vim: expandtab
from django.conf.urls import patterns, url

import views

urlpatterns = patterns('',
    url(r'^profile/$', views.profile, name='profile'),
    url(r'^login/$', 'django.contrib.auth.views.login', {'template_name': 'accounts/login.html'}, name='login'),
    url(r'^logout/$', 'django.contrib.auth.views.logout', {'template_name': 'accounts/logged_out.html'}, name='logout'),
)

