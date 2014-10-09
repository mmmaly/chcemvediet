# vim: expandtab
# -*- coding: utf-8 -*-
import hashlib
import hmac
import json
from base64 import b64encode

from django.core.exceptions import ImproperlyConfigured
from django.views.decorators.http import require_http_methods
from django.views.decorators.csrf import csrf_exempt
from django.http import HttpResponse, HttpResponseBadRequest, HttpResponseForbidden
from django.conf import settings

from poleno.utils.views import secure_required

from .signals import webhook_event

@require_http_methods([u'HEAD', u'POST'])
@csrf_exempt
@secure_required(raise_exception=True)
def webhook(request):
    # Based on djrill.views.DjrillWebhookView
    secret = getattr(settings, u'MANDRILL_WEBHOOK_SECRET', None)
    secret_name = getattr(settings, u'MANDRILL_WEBHOOK_SECRET_NAME', u'secret')
    webhook_keys = getattr(settings, u'MANDRILL_WEBHOOK_KEYS', None)
    webhook_url = getattr(settings, u'MANDRILL_WEBHOOK_URL', None)

    if not secret:
        raise ImproperlyConfigured(u'Setting MANDRILL_WEBHOOK_SECRET is not set.')
    if not webhook_url:
        raise ImproperlyConfigured(u'Setting MANDRILL_WEBHOOK_URL is not set.')
    if not webhook_keys and request.method == u'POST':
        raise ImproperlyConfigured(u'Setting MANDRILL_WEBHOOK_KEYS is not set.')

    if request.GET.get(secret_name) != secret:
        return HttpResponseForbidden(u'Secret does not match')

    if request.method == u'POST':
        signature = request.META.get(u'HTTP_X_MANDRILL_SIGNATURE', None)
        if not signature:
            return HttpResponseForbidden(u'X-Mandrill-Signature not set')

        post_parts = [webhook_url]
        post_lists = sorted(request.POST.lists())
        for key, value_list in post_lists:
            for item in value_list:
                post_parts.extend([key, item])
        post_string_encoded = u''.join(post_parts).encode('ascii','ignore')
        for webhook_key in webhook_keys:
            webhook_key_encoded = webhook_key.encode('ascii','ignore')
            hash_string = b64encode(hmac.new(key=webhook_key_encoded, msg=post_string_encoded, digestmod=hashlib.sha1).digest())
            if signature == hash_string:
                break
        else:
            return HttpResponseForbidden(u'Signature does not match')

        try:
            data = json.loads(request.POST.get(u'mandrill_events'))
        except TypeError:
            return HttpResponseBadRequest(u'Request syntax error')
        for event in data:
            webhook_event.send(sender=None, event_type=event['event'], data=event)

    return HttpResponse()
