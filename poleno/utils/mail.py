# vim: expandtab
# -*- coding: utf-8 -*-
from email.header import decode_header

from django.core.mail import EmailMultiAlternatives, EmailMessage
from django.template import TemplateDoesNotExist
from django.contrib.sites.models import Site

from poleno.utils.template import render_to_string
from poleno.utils.misc import squeeze


def render_mail(template_prefix, dictionary=None, **kwargs):
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
        render_mail('app/mail',
                    from_email='My Name <me@example.com>',
                    to=['Your Name <you@example.com>'])
    """
    site = Site.objects.get_current()
    subject = render_to_string(u'{}_subject.txt'.format(template_prefix), dictionary)
    subject = squeeze(u'[{}] {}'.format(site.name, subject))

    bodies = {}
    for ext in [u'html', u'txt']:
        template_name = u'{}_message.{}'.format(template_prefix, ext)
        try:
            bodies[ext] = render_to_string(template_name, dictionary).strip()
        except TemplateDoesNotExist:
            # We need at least one body
            if ext == u'txt' and not bodies:
                raise

    if u'txt' in bodies and u'html' in bodies:
        msg = EmailMultiAlternatives(subject, bodies[u'txt'], **kwargs)
        msg.attach_alternative(bodies[u'html'], u'text/html')
    elif u'html' in bodies:
        msg = EmailMessage(subject, bodies[u'html'], **kwargs)
        msg.content_subtype = u'html' # Main content is now text/html
    else:
        msg = EmailMessage(subject, bodies[u'txt'], **kwargs)

    return msg

def full_decode_header(header):
    u"""
    Use python ``email.header.decode_header`` function to decode email header parts, convert them
    to unicode and join them to single unicode string.
    """
    # FIXME: Decoding "=?UTF-8?...?=" fails sometimes. Eg. if it is followed with "\r\n". This
    # happens with local dummy email infrastructure used with Thunderbird for instance.
    # See http://stackoverflow.com/questions/20816766/python-email-header-decode-header-fails-for-multiline-headers
    if isinstance(header, str):
        header = header.encode(u'utf-8')
    parts = decode_header(header)
    decoded = u''.join(part.decode(enc or u'utf-8', u'replace') if isinstance(part, bytes) else part for part, enc in parts)
    return decoded
