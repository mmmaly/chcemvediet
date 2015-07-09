# vim: expandtab
# -*- coding: utf-8 -*-
from django.template.loader import render_to_string
from django.contrib import messages

def render_message(request, level, template, context=None, **kwargs):
    u"""
    Render the template and use the result to create and queue a ``django.contrib.messages``
    message.
    """
    message = render_to_string(template, context or {}).strip()
    messages.add_message(request, level, message, **kwargs)
