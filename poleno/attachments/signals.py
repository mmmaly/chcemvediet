# vim: expandtab
# -*- coding: utf-8 -*-
from django.dispatch import receiver
from django.db.models.signals import post_delete

from .models import Attachment

@receiver(post_delete, sender=Attachment)
def delete_file_on_attachment_post_delete(sender, instance, **kwargs):
    u"""
    Django ``FileField`` does not delete associated files when deleted. We need to delete them
    manually.
    """
    instance.file.delete(save=False)
