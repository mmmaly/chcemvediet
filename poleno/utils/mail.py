# vim: expandtab
# -*- coding: utf-8 -*-
import re

from django.core.mail import EmailMultiAlternatives, EmailMessage
from django.template.loader import render_to_string
from django.template import TemplateDoesNotExist
from django.contrib.sites.models import Site

from poleno.utils.misc import squeeze

def render_mail(template_prefix, dictionary=None, context_instance=None, **kwargs):
    u"""
    Create ``django.core.mail.EmailMessage`` object ready to be sent with ``msg.send()`` method.
    Message subject and body are rendered using templates "(prefix)_subject.txt" and
    "(prefix)_message.txt" and/or "(prefix)_message.html". If both ".txt" and ".html" body
    templates exist, the created message is multipart/alternativea including its text and html
    versions.

    The functions accepts additional keyword arguments for EmailMessage constructor. Of most
    interest are: ``from_email``, ``to``, ``bcc``, ``attachments``, ``headers`` and ``cc``.

    Based on: Django-allauth's allauth.DefaultAccountAdapter.render_mail method.

    Examples:
        render_mail('app/mail', from_email='My Name <me@example.com>', to=['Your Name <you@example.com>'])
    """
    site = Site.objects.get_current()
    subject = render_to_string(u'%s_subject.txt' % template_prefix, dictionary, context_instance)
    subject = squeeze(u'[%s] %s' % (site.name, subject))

    bodies = {}
    for ext in [u'html', u'txt']:
        template_name = u'%s_message.%s' % (template_prefix, ext)
        try:
            bodies[ext] = render_to_string(template_name, dictionary, context_instance).strip()
        except TemplateDoesNotExist:
            # We need at least one body
            if ext == u'txt' and not bodies:
                raise

    if u'txt' in bodies:
        msg = EmailMultiAlternatives(subject, bodies[u'txt'], **kwargs)
        if u'html' in bodies:
            msg.attach_alternative(bodies[u'html'], u'text/html')
    else:
        msg = EmailMessage(subject, bodies[u'html'], **kwargs)
        msg.content_subtype = u'html' # Main content is now text/html
    return msg
