# vim: expandtab
# -*- coding: utf-8 -*-

from django.conf.urls import patterns, url

import views

urlpatterns = patterns(u'',
    url(r'^$', views.upload, name=u'upload'),
    url(r'^(?P<attachment_id>\d+)/$', views.download, name=u'download'),
    url(r'^mail/(?P<attachment_id>\d+)/$', views.mail_download, name=u'mail_download'),
)

