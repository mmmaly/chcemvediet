# vim: expandtab
# -*- coding: utf-8 -*-
from django.conf import settings
from django.conf.urls import patterns, url
from django.utils.translation import ugettext_lazy as _

from . import views

urlpatterns = patterns(u'',
    url(r'^$', views.inforequest_index, name=u'index'),
    url(_(r'^create/$'), views.inforequest_create, name=u'create'),
    url(_(r'^create/(?P<draft_pk>\d+)/$'), views.inforequest_create, name=u'create_from_draft'),
    url(_(r'^detail/(?P<inforequest_pk>\d+)/$'), views.inforequest_detail, name=u'detail'),
    url(_(r'^delete-draft/(?P<draft_pk>\d+)/$'), views.inforequest_delete_draft, name=u'delete_draft'),
    url(_(r'^decide-email/confirmation/(?P<inforequest_pk>\d+)/(?P<email_pk>\d+)/$'), views.decide_email_confirmation, name=u'decide_email_confirmation'),
    url(_(r'^decide-email/extension/(?P<inforequest_pk>\d+)/(?P<email_pk>\d+)/$'), views.decide_email_extension, name=u'decide_email_extension'),
    url(_(r'^decide-email/advancement/(?P<inforequest_pk>\d+)/(?P<email_pk>\d+)/$'), views.decide_email_advancement, name=u'decide_email_advancement'),
    url(_(r'^decide-email/clarification-request/(?P<inforequest_pk>\d+)/(?P<email_pk>\d+)/$'), views.decide_email_clarification_request, name=u'decide_email_clarification_request'),
    url(_(r'^decide-email/disclosure/(?P<inforequest_pk>\d+)/(?P<email_pk>\d+)/$'), views.decide_email_disclosure, name=u'decide_email_disclosure'),
    url(_(r'^decide-email/refusal/(?P<inforequest_pk>\d+)/(?P<email_pk>\d+)/$'), views.decide_email_refusal, name=u'decide_email_refusal'),
    url(_(r'^decide-email/unrelated/(?P<inforequest_pk>\d+)/(?P<email_pk>\d+)/$'), views.decide_email_unrelated, name=u'decide_email_unrelated'),
    url(_(r'^decide-email/unknown/(?P<inforequest_pk>\d+)/(?P<email_pk>\d+)/$'), views.decide_email_unknown, name=u'decide_email_unknown'),
    url(_(r'^add-smail/confirmation/(?P<inforequest_pk>\d+)/$'), views.add_smail_confirmation, name=u'add_smail_confirmation'),
    url(_(r'^add-smail/extension/(?P<inforequest_pk>\d+)/$'), views.add_smail_extension, name=u'add_smail_extension'),
    url(_(r'^add-smail/advancement/(?P<inforequest_pk>\d+)/$'), views.add_smail_advancement, name=u'add_smail_advancement'),
    url(_(r'^add-smail/clarification-request/(?P<inforequest_pk>\d+)/$'), views.add_smail_clarification_request, name=u'add_smail_clarification_request'),
    url(_(r'^add-smail/disclosure/(?P<inforequest_pk>\d+)/$'), views.add_smail_disclosure, name=u'add_smail_disclosure'),
    url(_(r'^add-smail/refusal/(?P<inforequest_pk>\d+)/$'), views.add_smail_refusal, name=u'add_smail_refusal'),
    url(_(r'^add-smail/affirmation/(?P<inforequest_pk>\d+)/$'), views.add_smail_affirmation, name=u'add_smail_affirmation'),
    url(_(r'^add-smail/reversion/(?P<inforequest_pk>\d+)/$'), views.add_smail_reversion, name=u'add_smail_reversion'),
    url(_(r'^add-smail/remandment/(?P<inforequest_pk>\d+)/$'), views.add_smail_remandment, name=u'add_smail_remandment'),
    url(_(r'^new-action/clarification-response/(?P<inforequest_pk>\d+)/$'), views.new_action_clarification_response, name=u'new_action_clarification_response'),
    url(_(r'^new-action/appeal/(?P<inforequest_pk>\d+)/$'), views.new_action_appeal, name=u'new_action_appeal'),
    url(r'^(?P<inforequest_pk>\d+)/clarification-response/(?P<branch_pk>\d+)/$',                   views.clarification_response, name=u'clarification_response'),
    url(r'^(?P<inforequest_pk>\d+)/clarification-response/(?P<branch_pk>\d+)/(?P<step_idx>\d+)/$', views.clarification_response, name=u'clarification_response_step'),
    url(r'^(?P<inforequest_pk>\d+)/appeal/(?P<branch_pk>\d+)/$',                                   views.appeal,                 name=u'appeal'),
    url(r'^(?P<inforequest_pk>\d+)/appeal/(?P<branch_pk>\d+)/(?P<step_idx>\d+)/$',                 views.appeal,                 name=u'appeal_step'),
    url(_(r'^action/extend-deadline/(?P<inforequest_pk>\d+)/(?P<branch_pk>\d+)/(?P<action_pk>\d+)/$'), views.action_extend_deadline, name=u'action_extend_deadline'),
    url(_(r'^attachments/$'), views.attachment_upload, name=u'upload_attachment'),
    url(_(r'^attachments/(?P<attachment_pk>\d+)/$'), views.attachment_download, name=u'download_attachment'),
)

if settings.DEBUG: # pragma: no cover
    urlpatterns += patterns(u'',
        url(r'^devtools/mock-response/(?P<inforequest_pk>\d+)/$', views.devtools_mock_response, name=u'devtools_mock_response'),
        url(r'^devtools/undo-last-action/(?P<inforequest_pk>\d+)/$', views.devtools_undo_last_action, name=u'devtools_undo_last_action'),
        url(r'^devtools/push-history/(?P<inforequest_pk>\d+)/$', views.devtools_push_history, name=u'devtools_push_history'),
    )
