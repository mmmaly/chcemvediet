# vim: expandtab
# -*- coding: utf-8 -*-
from django.conf import settings
from django.conf.urls import patterns, url
from django.utils.translation import ugettext_lazy as _

from . import views

urlpatterns = patterns(u'',
    url(r'^$', views.inforequest.index, name=u'index'),
    url(_(r'^create/$'), views.inforequest.create, name=u'create'),
    url(_(r'^create/(?P<draft_pk>\d+)/$'), views.inforequest.create, name=u'create_from_draft'),
    url(_(r'^detail/(?P<inforequest_pk>\d+)/$'), views.inforequest.detail, name=u'detail'),
    url(_(r'^delete-draft/(?P<draft_pk>\d+)/$'), views.inforequest.delete_draft, name=u'delete_draft'),
    url(_(r'^decide-email/confirmation/(?P<inforequest_pk>\d+)/(?P<email_pk>\d+)/$'), views.decide_email.confirmation, name=u'decide_email_confirmation'),
    url(_(r'^decide-email/extension/(?P<inforequest_pk>\d+)/(?P<email_pk>\d+)/$'), views.decide_email.extension, name=u'decide_email_extension'),
    url(_(r'^decide-email/advancement/(?P<inforequest_pk>\d+)/(?P<email_pk>\d+)/$'), views.decide_email.advancement, name=u'decide_email_advancement'),
    url(_(r'^decide-email/clarification-request/(?P<inforequest_pk>\d+)/(?P<email_pk>\d+)/$'), views.decide_email.clarification_request, name=u'decide_email_clarification_request'),
    url(_(r'^decide-email/disclosure/(?P<inforequest_pk>\d+)/(?P<email_pk>\d+)/$'), views.decide_email.disclosure, name=u'decide_email_disclosure'),
    url(_(r'^decide-email/refusal/(?P<inforequest_pk>\d+)/(?P<email_pk>\d+)/$'), views.decide_email.refusal, name=u'decide_email_refusal'),
    url(_(r'^decide-email/unrelated/(?P<inforequest_pk>\d+)/(?P<email_pk>\d+)/$'), views.decide_email.unrelated, name=u'decide_email_unrelated'),
    url(_(r'^decide-email/unknown/(?P<inforequest_pk>\d+)/(?P<email_pk>\d+)/$'), views.decide_email.unknown, name=u'decide_email_unknown'),
    url(_(r'^add-smail/confirmation/(?P<inforequest_pk>\d+)/$'), views.add_smail.confirmation, name=u'add_smail_confirmation'),
    url(_(r'^add-smail/extension/(?P<inforequest_pk>\d+)/$'), views.add_smail.extension, name=u'add_smail_extension'),
    url(_(r'^add-smail/advancement/(?P<inforequest_pk>\d+)/$'), views.add_smail.advancement, name=u'add_smail_advancement'),
    url(_(r'^add-smail/clarification-request/(?P<inforequest_pk>\d+)/$'), views.add_smail.clarification_request, name=u'add_smail_clarification_request'),
    url(_(r'^add-smail/disclosure/(?P<inforequest_pk>\d+)/$'), views.add_smail.disclosure, name=u'add_smail_disclosure'),
    url(_(r'^add-smail/refusal/(?P<inforequest_pk>\d+)/$'), views.add_smail.refusal, name=u'add_smail_refusal'),
    url(_(r'^add-smail/affirmation/(?P<inforequest_pk>\d+)/$'), views.add_smail.affirmation, name=u'add_smail_affirmation'),
    url(_(r'^add-smail/reversion/(?P<inforequest_pk>\d+)/$'), views.add_smail.reversion, name=u'add_smail_reversion'),
    url(_(r'^add-smail/remandment/(?P<inforequest_pk>\d+)/$'), views.add_smail.remandment, name=u'add_smail_remandment'),
    url(_(r'^new-action/clarification-response/(?P<inforequest_pk>\d+)/$'), views.new_action.clarification_response, name=u'new_action_clarification_response'),
    url(_(r'^new-action/appeal/(?P<inforequest_pk>\d+)/$'), views.new_action.appeal, name=u'new_action_appeal'),
    url(_(r'^extend-deadline/(?P<inforequest_pk>\d+)/(?P<branch_pk>\d+)/(?P<action_pk>\d+)/$'), views.inforequest.extend_deadline, name=u'extend_deadline'),
    url(_(r'^attachments/$'), views.attachment.upload, name=u'upload_attachment'),
    url(_(r'^attachments/(?P<attachment_pk>\d+)/$'), views.attachment.download, name=u'download_attachment'),
)

if settings.DEBUG: # pragma: no cover
    urlpatterns += patterns(u'',
        url(r'^devtools/mock-response/(?P<inforequest_pk>\d+)/$', views.devtools.mock_response, name=u'devtools_mock_response'),
        url(r'^devtools/push_history/(?P<inforequest_pk>\d+)/$', views.devtools.push_history, name=u'devtools_push_history'),
    )
