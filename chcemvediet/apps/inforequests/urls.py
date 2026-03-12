# vim: expandtab
# -*- coding: utf-8 -*-
from django.conf import settings
from django.urls import re_path
from django.utils.translation import gettext_lazy as _

from poleno.utils.urls import reverse_adaptor, reverse
from poleno.utils.lazy import lazy_concat, lazy_format

from . import views


parts = {
    u'inforequest_pk':            r'(?P<inforequest_pk>\d+)/',
    u'inforequest_slug_pk':    r'(?:(?P<inforequest_slug>[a-z0-9-]+)-)?(?P<inforequest_pk>\d+)/',
    u'branch_pk':                 r'(?P<branch_pk>\d+)/',
    u'action_pk':                 r'(?P<action_pk>\d+)/',
    u'draft_pk':                  r'(?P<draft_pk>\d+)/',
    u'draft_pk?':              r'(?:(?P<draft_pk>\d+)/)?',
    u'attachment_pk':             r'(?P<attachment_pk>\d+)/',
    u'attachment_finalization_pk':r'(?P<attachment_finalization_pk>\d+)/',
    u'step_idx':                  r'(?P<step_idx>\d+)/',
    u'step_idx?':              r'(?:(?P<step_idx>\d+)/)?',
    u'mine':                      lazy_concat(_(u'inforequests:urls:mine'), u'/'),
    u'create':                    lazy_concat(_(u'inforequests:urls:create'), u'/'),
    u'delete_draft':              lazy_concat(_(u'inforequests:urls:delete_draft'), u'/'),
    u'obligee_action':            lazy_concat(_(u'inforequests:urls:obligee_action'), u'/'),
    u'obligee_action_dispatcher': lazy_concat(_(u'inforequests:urls:obligee_action_dispatcher'), u'/'),
    u'clarification_response':    lazy_concat(_(u'inforequests:urls:clarification_response'), u'/'),
    u'appeal':                    lazy_concat(_(u'inforequests:urls:appeal'), u'/'),
    u'snooze':                    lazy_concat(_(u'inforequests:urls:snooze'), u'/'),
    u'attachments':               lazy_concat(_(u'inforequests:urls:attachments'), u'/'),
    u'attachment_finalizations':  lazy_concat(_(u'inforequests:urls:attachment_finalizations'), u'/'),
    u'feedback_action':           lazy_concat(_(u'inforequests:urls:feedback_action'), u'/')
    }

app_name = u'inforequests'

urlpatterns = [
    re_path(lazy_format(r'^$'),                                                                             views.inforequest_index,                name=u'index'),
    re_path(lazy_format(r'^{mine}$', **parts),                                                              views.inforequest_mine,                 name=u'mine'),
    re_path(lazy_format(r'^{create}{draft_pk?}$', **parts),                                                 views.inforequest_create,               name=u'create'),
    re_path(lazy_format(r'^{delete_draft}{draft_pk}$', **parts),                                            views.inforequest_delete_draft,         name=u'delete_draft'),
    re_path(lazy_format(r'^{obligee_action_dispatcher}$', **parts),                                         views.obligee_action_dispatcher,        name=u'obligee_action_dispatcher'),
    re_path(lazy_format(r'^{inforequest_slug_pk}$', **parts),                                               views.inforequest_detail,               name=u'detail'),
    re_path(lazy_format(r'^{inforequest_slug_pk}{obligee_action}{step_idx?}$', **parts),                    views.obligee_action,                   name=u'obligee_action'),
    re_path(lazy_format(r'^{inforequest_slug_pk}{clarification_response}{branch_pk}{step_idx?}$', **parts), views.clarification_response,           name=u'clarification_response'),
    re_path(lazy_format(r'^{inforequest_slug_pk}{appeal}{branch_pk}{step_idx?}$', **parts),                 views.appeal,                           name=u'appeal'),
    re_path(lazy_format(r'^{inforequest_slug_pk}{snooze}{branch_pk}{action_pk}$', **parts),                 views.snooze,                           name=u'snooze'),
    re_path(lazy_format(r'^{inforequest_slug_pk}{feedback_action}{step_idx?}$', **parts),                    views.feedback_action,                  name=u'feedback_action'),
    re_path(lazy_format(r'^{attachments}$', **parts),                                                       views.attachment_upload,                name=u'upload_attachment'),
    re_path(lazy_format(r'^{attachments}{attachment_pk}$', **parts),                                        views.attachment_download,              name=u'download_attachment'),
    re_path(lazy_format(r'^{attachment_finalizations}{attachment_finalization_pk}$', **parts),              views.attachment_finalization_download, name=u'download_attachment_finalization'),
]

if settings.DEBUG: # pragma: no cover
    urlpatterns += [
        re_path(lazy_format(r'^devtools/mock-response/{inforequest_pk}$', **parts),    views.devtools_mock_response,    name=u'devtools_mock_response'),
        re_path(lazy_format(r'^devtools/undo-last-action/{inforequest_pk}$', **parts), views.devtools_undo_last_action, name=u'devtools_undo_last_action'),
        re_path(lazy_format(r'^devtools/push-history/{inforequest_pk}$', **parts),     views.devtools_push_history,     name=u'devtools_push_history'),
        re_path(lazy_format(r'^devtools/delete/{inforequest_pk}$', **parts),           views.devtools_delete,           name=u'devtools_delete'),
    ]


@reverse_adaptor(u'inforequests:create', u'draft')
@reverse_adaptor(u'inforequests:delete_draft', u'draft')
def draft_adaptor(draft):
    return dict(draft_pk=draft.pk)

@reverse_adaptor(u'inforequests:detail', u'inforequest')
@reverse_adaptor(u'inforequests:obligee_action', u'inforequest')
@reverse_adaptor(u'inforequests:feedback_action', u'inforequest')
def inforequest_adaptor_slug_and_pk(inforequest):
    return dict(
            inforequest_slug=inforequest.slug,
            inforequest_pk=inforequest.pk,
            )

@reverse_adaptor(u'inforequests:devtools_mock_response', u'inforequest')
@reverse_adaptor(u'inforequests:devtools_undo_last_action', u'inforequest')
@reverse_adaptor(u'inforequests:devtools_push_history', u'inforequest')
@reverse_adaptor(u'inforequests:devtools_delete', u'inforequest')
def inforequest_adaptor_pk(inforequest):
    return dict(
            inforequest_pk=inforequest.pk,
            )

@reverse_adaptor(u'inforequests:clarification_response', u'branch')
@reverse_adaptor(u'inforequests:appeal', u'branch')
def branch_adaptor(branch):
    return dict(
            inforequest_slug=branch.inforequest.slug,
            inforequest_pk=branch.inforequest.pk,
            branch_pk=branch.pk,
            )

@reverse_adaptor(u'inforequests:snooze', u'action')
def action_adaptor(action):
    return dict(
            inforequest_slug=action.branch.inforequest.slug,
            inforequest_pk=action.branch.inforequest.pk,
            branch_pk=action.branch.pk,
            action_pk=action.pk,
            )

@reverse_adaptor(u'inforequests:download_attachment', u'attachment')
def attachment_adaptor(attachment):
    return dict(attachment_pk=attachment.pk)

@reverse_adaptor(u'inforequests:download_attachment_finalization', u'attachment_finalization')
def attachment_finalization_adaptor(attachment_finalization):
    return dict(attachment_finalization_pk=attachment_finalization.pk)

@reverse_adaptor(u'inforequests:obligee_action', u'step')
@reverse_adaptor(u'inforequests:feedback_action', u'step')
@reverse_adaptor(u'inforequests:clarification_response', u'step')
@reverse_adaptor(u'inforequests:appeal', u'step')
def step_adaptor(step):
    return dict(step_idx=step.index)
