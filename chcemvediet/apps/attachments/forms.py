# vim: expandtab
# -*- coding: utf-8 -*-
from django import forms
from django.core.exceptions import ValidationError
from django.template.loader import render_to_string
from django.utils.translation import ugettext_lazy as _

from models import Attachment

class AttachmentsWidget(forms.TextInput):
    def render(self, name, value, attrs=None):
        textinput_value = u',%s,' % u','.join(u'%s' % a.pk for a in value or [])
        textinput = super(AttachmentsWidget, self).render(name, textinput_value, attrs)
        return render_to_string(u'attachments/attachments_widget.html', {
                u'name': name,
                u'textinput': textinput,
                u'attachments': value or [],
                })

class AttachmentsField(forms.Field):
    widget = AttachmentsWidget

    def __init__(self, *args, **kwargs):
        self.owner = kwargs.pop(u'owner', None)
        super(AttachmentsField, self).__init__(*args, **kwargs)

    def prepare_value(self, value):
        if isinstance(value, basestring):
            try:
                return self.to_python(value)
            except ValidationError:
                return None
        return value

    def to_python(self, value):
        u""" Returns list of Attachments """
        keys = filter(None, value.split(u','))
        if not keys:
            return []

        # We dont check whether the attachments were uploaded by this very same form field. We only
        # check if they were uploaded by the same user. Unsolicited user may plant id of any
        # attachment he uploaded earlier and "hijack" it. However, he only can "hijack" his own
        # attachments, which he can download and reupload manually anyway. So it's not an issue.
        if not self.owner:
            raise ValueError
        query_set = Attachment.objects.owned_by(self.owner)
        try:
            attachments = query_set.filter(pk__in=keys)
        except ValueError:
            raise ValidationError(_(u'Invalid attachments.'))

        # Primary keys are unique, so ``filter(pk__in=keys)`` gets at most one attachment for every
        # key. Therefore, if any key is wrong, we must get fewer than ``len(keys)`` attachments.
        # Or, in other words, if we get ``len(keys)`` attachments, every key mached.
        if len(attachments) != len(keys):
            raise ValidationError(_(u'Invalid attachments.'))

        return attachments


