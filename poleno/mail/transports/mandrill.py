# vim: expandtab
# -*- coding: utf-8 -*-
import json
import base64
import requests

from django.core.exceptions import ImproperlyConfigured
from django.conf import settings

from base import BaseTransport

class MandrillTransport(BaseTransport):
    def __init__(self, **kwargs):
        super(MandrillTransport, self).__init__(**kwargs)
        self.api_key = getattr(settings, u'MANDRILL_API_KEY')
        self.api_url = getattr(settings, u'MANDRILL_API_URL', u'https://mandrillapp.com/api/1.0')
        self.api_send = self.api_url + u'/messages/send.json'

    def send_message(self, message):
        assert message.type == message.TYPES.OUTBOUND
        assert message.processed is None

        # Based on djrill.mail.backends.DjrillBackend; We can't use Djrill directly because it
        # sends the mail synchronously during user requests.
        msg = {}
        msg[u'subject'] = message.subject
        msg[u'from_email'] = message.from_mail
        if message.from_name:
            msg[u'from_name'] = message.from_name
        if message.html:
            msg[u'html'] = message.html
        if message.text:
            msg[u'text'] = message.text
        if message.headers:
            msg[u'headers'] = message.headers

        msg[u'to'] = []
        for recipient in message.recipient_set.all():
            rcp = {}
            rcp[u'email'] = recipient.mail
            if recipient.name:
                rcp[u'name'] = recipient.name
            if recipient.type == recipient.TYPES.TO:
                rcp[u'type'] = u'to'
            elif recipient.type == recipient.TYPES.CC:
                rcp[u'type'] = u'cc'
            elif recipient.type == recipient.TYPES.BCC:
                rcp[u'type'] = u'bcc'
            else:
                continue
            msg[u'to'].append(rcp)

        msg[u'attachments'] = []
        for attachment in message.attachment_set.all():
            attch = {}
            attch[u'type'] = attachment.content_type
            attch[u'name'] = attachment.name
            attch[u'content'] = base64.b64encode(attachment.content)
            msg[u'attachments'].append(attch)

        data = {}
        data[u'key'] = self.api_key
        data[u'message'] = msg

        response = requests.post(self.api_send, data=json.dumps(data))

        if response.status_code != 200:
            raise RuntimeError(u'Sending Message(pk=%s) failed with status code %s. Mandrill response: %s' %
                    (message.pk, response.status_code, response.text))

        for rcp in response.json():
            for recipient in message.recipient_set.filter(mail=rcp[u'email']):
                recipient.remote_id = rcp[u'_id']

                if rcp[u'status'] == u'sent':
                    recipient.status = recipient.STATUSES.SENT
                elif rcp[u'status'] == u'queued' or rcp[u'status'] == u'scheduled':
                    recipient.status = recipient.STATUSES.QUEUED
                elif rcp[u'status'] == u'rejected':
                    recipient.status = recipient.STATUSES.REJECTED
                    recipient.status_details = rcp[u'reject_reason']
                elif rcp[u'status'] == u'invalid':
                    recipient.status = recipient.STATUSES.INVALID
                else:
                    recipient.status = recipient.STATUSES.UNDEFINED

                recipient.save()
