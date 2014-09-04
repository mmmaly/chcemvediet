# vim: expandtab
# -*- coding: utf-8 -*-
from django.conf.urls import patterns, url
from django.utils.translation import ugettext_lazy as _

import views

urlpatterns = patterns(u'',
    url(r'^$', views.index, name=u'index'),
    url(_(r'^create/$'), views.create, name=u'create'),
    url(_(r'^create/(?P<draft_id>\d+)/$'), views.create, name=u'create_from_draft'),
    url(_(r'^detail/(?P<inforequest_id>\d+)/$'), views.detail, name=u'detail'),
    url(_(r'^delete-draft/(?P<draft_id>\d+)/$'), views.delete_draft, name=u'delete_draft'),
    url(_(r'^decide-email/(?P<action>[\w-]+)/(?P<inforequest_id>\d+)/(?P<receivedemail_id>\d+)/$'), views.decide_email, name=u'decide_email'),
    url(_(r'^add-smail/(?P<action>[\w-]+)/(?P<inforequest_id>\d+)/$'), views.add_smail, name=u'add_smail'),
    url(_(r'^new-action/(?P<action>[\w-]+)/(?P<inforequest_id>\d+)/$'), views.new_action, name=u'new_action'),
)

