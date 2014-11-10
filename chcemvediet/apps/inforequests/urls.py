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
    url(_(r'^extend-deadline/(?P<inforequest_pk>\d+)/(?P<paperwork_pk>\d+)/(?P<action_pk>\d+)/$'), views.extend_deadline, name=u'extend_deadline'),
    url(_(r'^attachments/$'), views.upload_attachment, name=u'upload_attachment'),
    url(_(r'^attachments/(?P<attachment_pk>\d+)/$'), views.download_attachment, name=u'download_attachment'),
)
