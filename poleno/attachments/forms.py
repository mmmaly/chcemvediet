# vim: expandtab
# -*- coding: utf-8 -*-
import collections
import collections.abc

from django import forms
from django.core.exceptions import ValidationError
from django.utils.translation import gettext_lazy as _

from poleno.utils.template import render_to_string
from poleno.utils.misc import cached_method, filesize

from .models import Attachment


class AttachmentsWidget(forms.TextInput):

    def __init__(self, *args, **kwargs):
        super(AttachmentsWidget, self).__init__(*args, **kwargs)
        self.upload_url_func = None
        self.download_url_func = None

    def render(self, name, value, attrs=None):
        textinput_value = u',{},'.format(u','.join(format(a.pk) for a in value or []))
        textinput_attrs = dict(attrs, type=u'hidden')
        textinput = super(AttachmentsWidget, self).render(name, textinput_value, textinput_attrs)
        return render_to_string(u'attachments/attachments_widget.html', {
                u'name': name,
                u'textinput': textinput,
                u'attachments': value or [],
                u'funcs': {
                    u'upload_url': self.upload_url_func,
                    u'download_url': self.download_url_func,
                    },
                })

class AttachmentsField(forms.Field):
    widget = AttachmentsWidget

    def __init__(self, *args, **kwargs):
        max_count = kwargs.pop(u'max_count', None)
        max_size = kwargs.pop(u'max_size', None)
        max_total_size = kwargs.pop(u'max_total_size', None)
        attached_to = kwargs.pop(u'attached_to', None)
        upload_url_func = kwargs.pop(u'upload_url_func', None)
        download_url_func = kwargs.pop(u'download_url_func', None)
        super(AttachmentsField, self).__init__(*args, **kwargs)

        self._upload_url_func = None
        self._download_url_func = None

        self.max_count = max_count
        self.max_size = max_size
        self.max_total_size = max_total_size
        self.attached_to = attached_to
        self.upload_url_func = upload_url_func
        self.download_url_func = download_url_func

    @property
    def upload_url_func(self):
        return self._upload_url_func

    @upload_url_func.setter
    def upload_url_func(self, func):
        self.widget.upload_url_func = self._upload_url_func = func

    @property
    def download_url_func(self):
        return self._download_url_func

    @download_url_func.setter
    def download_url_func(self, func):
        self.widget.download_url_func = self._download_url_func = func

    def prepare_value(self, value):
        if isinstance(value, str):
            try:
                return self.to_python(value)
            except ValidationError:
                return None
        return value

    @cached_method(cached_exceptions=ValidationError)
    def to_python(self, value):
        u""" Returns list of Attachments """
        if value is None:
            return []
        keys = [k for k in value.split(u',') if k]
        if not keys:
            return []

        # Only attachments poiting to whitelisted objects may be used by the field.
        if isinstance(self.attached_to, collections.abc.Iterable):
            query_set = Attachment.objects.attached_to(*self.attached_to)
        else:
            query_set = Attachment.objects.attached_to(self.attached_to)

        try:
            attachments = query_set.filter(pk__in=keys).order_by_pk()
        except ValueError:
            raise ValidationError(_(u'attachments:AttachmentsField:error:invalid'))
        if len(attachments) != len(keys):
            raise ValidationError(_(u'attachments:AttachmentsField:error:invalid'))
        return attachments

    def validate(self, value):
        super(AttachmentsField, self).validate(value)

        if self.max_count is not None and len(value) > self.max_count:
            msg = _(u'attachments:AttachmentsField:error:max_count')
            raise ValidationError(msg.format(max_count=self.max_count, count=len(value)))

        if self.max_size is not None:
            for attachment in value:
                if attachment.size > self.max_size:
                    msg = _(u'attachments:AttachmentsField:error:max_size')
                    raise ValidationError(msg.format(
                            max_size=filesize(self.max_size),
                            size=filesize(attachment.size),
                            attachment=attachment,
                            ))

        if self.max_total_size is not None:
            total_size = sum(a.size for a in value)
            if total_size > self.max_total_size:
                msg = _(u'attachments:AttachmentsField:error:max_total_size')
                raise ValidationError(msg.format(
                        max_total_size=filesize(self.max_total_size),
                        total_size=filesize(total_size),
                        ))
