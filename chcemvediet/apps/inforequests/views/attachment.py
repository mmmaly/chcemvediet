# vim: expandtab
# -*- coding: utf-8 -*-
from django.db import transaction
from django.db.models import Q
from django.views.decorators.http import require_http_methods
from django.http import Http404
from django.contrib.sessions.models import Session

from poleno.attachments import views as attachments_views
from poleno.attachments.models import Attachment
from poleno.mail.models import Message
from poleno.utils.urls import reverse
from poleno.utils.views import require_ajax, login_required
from chcemvediet.apps.wizards.models import WizardDraft
from chcemvediet.apps.inforequests.models import InforequestDraft, Action
from chcemvediet.apps.anonymization.anonymization import generate_user_pattern, anonymize_string
from chcemvediet.apps.anonymization.models import AttachmentFinalization


@require_http_methods([u'POST'])
@require_ajax
@transaction.atomic
@login_required(raise_exception=True)
def attachment_upload(request):
    session = Session.objects.get(session_key=request.session.session_key)
    download_url_func = (lambda a: reverse(u'inforequests:download_attachment', args=[a.pk]))
    return attachments_views.upload(request, session, download_url_func)

@require_http_methods([u'HEAD', u'GET'])
def attachment_download(request, attachment_pk):
    if request.user.is_anonymous:
        permitted = {
                Action: Q(branch__inforequest__published=True) &
                        Q(branch__inforequest__applicant__profile__anonymize_inforequests=False),
                }
    else:
        permitted = {
                Session: Q(session_key=request.session.session_key),
                Message: Q(inforequest__applicant=request.user),
                WizardDraft: Q(owner=request.user),
                InforequestDraft: Q(applicant=request.user),
                Action: Q(branch__inforequest__applicant=request.user) | (
                            Q(branch__inforequest__published=True) &
                            Q(branch__inforequest__applicant__profile__anonymize_inforequests=False)
                        ),
                }

    attachment = Attachment.objects.get_or_404(pk=attachment_pk)
    attached_to_class = attachment.generic_type.model_class()

    try:
        condition = permitted[attached_to_class]
    except KeyError:
        raise Http404()

    try:
        attached_to_class.objects.filter(condition).get(pk=attachment.generic_id)
    except attached_to_class.DoesNotExist:
        raise Http404()

    return attachments_views.download(request, attachment)

@require_http_methods([u'HEAD', u'GET'])
def attachment_finalization_download(request, attachment_finalization_pk):
    attachment_finalization = AttachmentFinalization.objects.successful().get_or_404(
            pk=attachment_finalization_pk)
    generic_object = attachment_finalization.attachment.generic_object
    if isinstance(generic_object, Action):
        if generic_object.branch.inforequest.published:
            prog = generate_user_pattern(generic_object.branch.inforequest, match_subwords=True)
            filename = anonymize_string(prog, attachment_finalization.name)
            return attachments_views.download(request, attachment_finalization, filename)
    raise Http404()
