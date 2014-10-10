# vim: expandtab
# -*- coding: utf-8 -*-
from django.conf.urls import patterns, url
from django.utils.translation import ugettext_lazy as _

from . import views

urlpatterns = patterns(u'',
    url(r'^$', views.index, name=u'index'),
    url(_(r'^create/$'), views.create, name=u'create'),
    url(_(r'^create/(?P<draft_pk>\d+)/$'), views.create, name=u'create_from_draft'),
    url(_(r'^detail/(?P<inforequest_pk>\d+)/$'), views.detail, name=u'detail'),
    url(_(r'^delete-draft/(?P<draft_pk>\d+)/$'), views.delete_draft, name=u'delete_draft'),
    url(_(r'^decide-email/(?P<action>[\w-]+)/(?P<inforequest_pk>\d+)/(?P<email_pk>\d+)/$'), views.decide_email, name=u'decide_email'),
    url(_(r'^add-smail/(?P<action>[\w-]+)/(?P<inforequest_pk>\d+)/$'), views.add_smail, name=u'add_smail'),
    url(_(r'^new-action/(?P<action>[\w-]+)/(?P<inforequest_pk>\d+)/$'), views.new_action, name=u'new_action'),
    url(_(r'^extend-deadline/(?P<inforequest_pk>\d+)/(?P<paperwork_pk>\d+)/(?P<action_pk>\d+)/$'), views.extend_deadline, name=u'extend_deadline'),
    url(_(r'^attachments/$'), views.upload_attachment, name=u'upload_attachment'),
    url(_(r'^attachments/(?P<attachment_pk>\d+)/$'), views.download_attachment, name=u'download_attachment'),
)

