# vim: expandtab
# -*- coding: utf-8 -*-
from django.conf import settings
from django.conf.urls import patterns, url
from django.utils.translation import ugettext_lazy as _

from . import views

parts = {
    u'inforequest_pk': r'(?P<inforequest_pk>\d+)',
    u'branch_pk': r'(?P<branch_pk>\d+)',
    u'step_idx': r'(?:/(?P<step_idx>\d+))?',
    }

urlpatterns = patterns(u'',
    url(r'^$', views.inforequest_index, name=u'index'),
    url(_(r'^create/$'), views.inforequest_create, name=u'create'),
    url(_(r'^create/(?P<draft_pk>\d+)/$'), views.inforequest_create, name=u'create_from_draft'),
    url(_(r'^detail/(?P<inforequest_pk>\d+)/$'), views.inforequest_detail, name=u'detail'),
    url(_(r'^delete-draft/(?P<draft_pk>\d+)/$'), views.inforequest_delete_draft, name=u'delete_draft'),
    url(r'^{inforequest_pk}/obligee-action{step_idx}/$'.format(**parts),                     views.obligee_action,         name=u'obligee_action'),
    url(r'^{inforequest_pk}/clarification-response/{branch_pk}{step_idx}/$'.format(**parts), views.clarification_response, name=u'clarification_response'),
    url(r'^{inforequest_pk}/appeal/{branch_pk}{step_idx}/$'.format(**parts),                 views.appeal,                 name=u'appeal'),
    url(_(r'^extend-deadline/(?P<inforequest_pk>\d+)/(?P<branch_pk>\d+)/(?P<action_pk>\d+)/$'), views.extend_deadline, name=u'extend_deadline'),
    url(_(r'^attachments/$'), views.attachment_upload, name=u'upload_attachment'),
    url(_(r'^attachments/(?P<attachment_pk>\d+)/$'), views.attachment_download, name=u'download_attachment'),
)

if settings.DEBUG: # pragma: no cover
    urlpatterns += patterns(u'',
        url(r'^devtools/mock-response/(?P<inforequest_pk>\d+)/$', views.devtools_mock_response, name=u'devtools_mock_response'),
        url(r'^devtools/undo-last-action/(?P<inforequest_pk>\d+)/$', views.devtools_undo_last_action, name=u'devtools_undo_last_action'),
        url(r'^devtools/push-history/(?P<inforequest_pk>\d+)/$', views.devtools_push_history, name=u'devtools_push_history'),
    )
