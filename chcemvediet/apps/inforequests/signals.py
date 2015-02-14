# vim: expandtab
# -*- coding: utf-8 -*-
import operator

from django.dispatch import receiver
from django.db.models import Q
from django.db.models.signals import pre_delete
from django.conf import settings
from django.contrib.sessions.models import Session

from poleno.attachments.models import Attachment
from poleno.mail.signals import message_received
from poleno.utils.translation import translation

from .models import Inforequest, InforequestEmail

@receiver(message_received)
def assign_email_on_message_received(sender, message, **kwargs):
    if message.received_for:
        q = Q(unique_email__iexact=message.received_for)
    elif message.recipient_set.exists():
        q = (Q(unique_email__iexact=r.mail) for r in message.recipient_set.all())
        q = reduce(operator.or_, q)
    else:
        return

    try:
        inforequest = Inforequest.objects.get(q)
    except (Inforequest.DoesNotExist, Inforequest.MultipleObjectsReturned):
        return

    inforequestemail = InforequestEmail(
            inforequest=inforequest,
            email=message,
            type=InforequestEmail.TYPES.UNDECIDED,
            )
    inforequestemail.save()

    if not inforequest.closed:
        with translation(settings.LANGUAGE_CODE):
            inforequest.send_received_email_notification(message)

@receiver(pre_delete, sender=Session)
def delete_attachments_on_session_pre_delete(sender, instance, **kwargs):
    u"""
    Djago ``Session`` model does not define a reverse generic relation to ``Attachment``. Therefore
    session attachments are not deleted with the session automatically. We need to delete them
    manually.
    """
    Attachment.objects.attached_to(instance).delete()
