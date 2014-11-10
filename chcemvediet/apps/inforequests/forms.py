# vim: expandtab
# -*- coding: utf-8 -*-
from dateutil.relativedelta import relativedelta

from django import forms
from django.core.urlresolvers import reverse
from django.core.exceptions import ValidationError
from django.template.loader import render_to_string
from django.utils.translation import ugettext_lazy as _, pgettext_lazy
from django.utils.encoding import smart_text
from django.contrib.webdesign.lorem_ipsum import paragraphs as lorem

from poleno.attachments.forms import AttachmentsField
from poleno.utils.models import after_saved
from poleno.utils.forms import AutoSuppressedSelect, PrefixedForm
from poleno.utils.misc import squeeze
from poleno.utils.date import local_today
from chcemvediet.apps.obligees.forms import ObligeeWithAddressInput, ObligeeAutocompleteField

from .models import Paperwork, Action


class InforequestForm(PrefixedForm):
    obligee = ObligeeAutocompleteField(
            label=_(u'Obligee'),
            widget=ObligeeWithAddressInput(attrs={
                u'placeholder': _(u'Obligee'),
                }),
            )
    subject = forms.CharField(
            label=_(u'Subject'),
            initial=_(u'Information request'),
            max_length=255,
            widget=forms.TextInput(attrs={
                u'placeholder': _(u'Subject'),
                }),
            )
    content = forms.CharField(
            label=_(u'Request'),
            initial=lorem(1)[0],
            widget=forms.Textarea(attrs={
                u'placeholder': _(u'Request'),
                u'class': u'input-block-level',
                }),
            )
    attachments = AttachmentsField(
            label=_(u'Attachments'),
            required=False,
            upload_url_func=(lambda: reverse(u'inforequests:upload_attachment')),
            download_url_func=(lambda a: reverse(u'inforequests:download_attachment', args=(a.pk,))),
            )

    def __init__(self, *args, **kwargs):
        self.draft = kwargs.pop(u'draft', False)
        self.attached_to = kwargs.pop(u'attached_to')
        super(InforequestForm, self).__init__(*args, **kwargs)

        self.fields[u'attachments'].attached_to = self.attached_to

        if self.draft:
            self.fields[u'obligee'].required = False
            self.fields[u'subject'].required = False
            self.fields[u'content'].required = False

    def save(self, inforequest):
        assert self.is_valid()

        @after_saved(inforequest)
        def deferred():
            paperwork = Paperwork(
                    obligee=self.cleaned_data[u'obligee'],
                    inforequest=inforequest,
                    )
            paperwork.save()

            action = Action(
                    paperwork=paperwork,
                    subject=self.cleaned_data[u'subject'],
                    content=self.cleaned_data[u'content'],
                    effective_date=inforequest.submission_date,
                    type=Action.TYPES.REQUEST,
                    )
            action.save()

            action.attachment_set = self.cleaned_data[u'attachments']

    def save_to_draft(self, draft):
        assert self.is_valid()

        draft.obligee = self.cleaned_data[u'obligee']
        draft.subject = self.cleaned_data[u'subject']
        draft.content = self.cleaned_data[u'content']

        @after_saved(draft)
        def deferred():
            draft.attachment_set = self.cleaned_data[u'attachments']

    def load_from_draft(self, draft):
        self.initial[u'obligee'] = draft.obligee
        self.initial[u'subject'] = draft.subject
        self.initial[u'content'] = draft.content
        self.initial[u'attachments'] = draft.attachment_set.all()


class ActionAbstractForm(PrefixedForm):
    paperwork = forms.TypedChoiceField(
            label=_(u'Obligee'),
            empty_value=None,
            widget=AutoSuppressedSelect(suppressed_attrs={
                u'class': u'suppressed-control',
                }),
            )

    def __init__(self, *args, **kwargs):
        self.inforequest = kwargs.pop(u'inforequest')
        self.action_type = kwargs.pop(u'action_type')
        self.draft = kwargs.pop(u'draft', False)
        super(ActionAbstractForm, self).__init__(*args, **kwargs)

        # Assumes that converting a Paperwork to a string gives its ``pk``
        field = self.fields[u'paperwork']
        field.choices = [(paperwork, paperwork.historicalobligee.name)
                for paperwork in self.inforequest.paperwork_set.all()
                if paperwork.can_add_action(self.action_type)]
        if len(field.choices) > 1:
            field.choices = [(u'', u'')] + field.choices

        def coerce(val):
            for o, v in field.choices:
                if o and smart_text(o.pk) == val:
                    return o
            raise ValueError
        field.coerce = coerce

        if self.draft:
            self.fields[u'paperwork'].required = False

    def save(self, action):
        assert self.is_valid()
        action.paperwork = self.cleaned_data[u'paperwork']

    def save_to_draft(self, draft):
        assert self.is_valid()
        draft.paperwork = self.cleaned_data[u'paperwork']

    def load_from_draft(self, draft):
        self.initial[u'paperwork'] = draft.paperwork

class EffectiveDateMixin(ActionAbstractForm):
    effective_date = forms.DateField(
            label=_(u'Effective Date'),
            localize=True,
            widget=forms.DateInput(attrs={
                u'placeholder': pgettext_lazy(u'Form Date Placeholder', u'mm/dd/yyyy'),
                u'class': u'datepicker',
                }),
            )

    def __init__(self, *args, **kwargs):
        super(EffectiveDateMixin, self).__init__(*args, **kwargs)
        if self.draft:
            self.fields[u'effective_date'].required = False

    def clean(self):
        cleaned_data = super(EffectiveDateMixin, self).clean()

        if not self.draft:
            paperwork = cleaned_data.get(u'paperwork', None)
            effective_date = cleaned_data.get(u'effective_date', None)
            if effective_date:
                try:
                    if paperwork and effective_date < paperwork.last_action.effective_date:
                        raise ValidationError(_(u'May not be older than previous action.'))
                    if effective_date > local_today():
                        raise ValidationError(_(u'May not be from future.'))
                    if effective_date < local_today() - relativedelta(months=1):
                        raise ValidationError(_(u'May not be older than one month.'))
                except ValidationError as e:
                    self._errors[u'effective_date'] = self.error_class(e.messages)
                    del cleaned_data[u'effective_date']

        return cleaned_data

    def save(self, action):
        super(EffectiveDateMixin, self).save(action)
        action.effective_date = self.cleaned_data[u'effective_date']

    def save_to_draft(self, draft):
        super(EffectiveDateMixin, self).save_to_draft(draft)
        draft.effective_date = self.cleaned_data[u'effective_date']

    def load_from_draft(self, draft):
        super(EffectiveDateMixin, self).load_from_draft(draft)
        self.initial[u'effective_date'] = draft.effective_date

class SubjectContentMixin(ActionAbstractForm):
    subject = forms.CharField(
            label=_(u'Subject'),
            max_length=255,
            widget=forms.TextInput(attrs={
                u'placeholder': _(u'Subject'),
                }),
            )
    content = forms.CharField(
            label=_(u'Content'),
            widget=forms.Textarea(attrs={
                u'placeholder': _(u'Content'),
                u'class': u'input-block-level',
                }),
            )

    def __init__(self, *args, **kwargs):
        super(SubjectContentMixin, self).__init__(*args, **kwargs)
        if self.draft:
            self.fields[u'subject'].required = False
            self.fields[u'content'].required = False

    def save(self, action):
        super(SubjectContentMixin, self).save(action)
        action.subject = self.cleaned_data[u'subject']
        action.content = self.cleaned_data[u'content']

    def save_to_draft(self, draft):
        super(SubjectContentMixin, self).save_to_draft(draft)
        draft.subject = self.cleaned_data[u'subject']
        draft.content = self.cleaned_data[u'content']

    def load_from_draft(self, draft):
        super(SubjectContentMixin, self).load_from_draft(draft)
        self.initial[u'subject'] = draft.subject
        self.initial[u'content'] = draft.content

class AttachmentsMixin(ActionAbstractForm):
    attachments = AttachmentsField(
            label=_(u'Attachments'),
            required=False,
            upload_url_func=(lambda: reverse(u'inforequests:upload_attachment')),
            download_url_func=(lambda a: reverse(u'inforequests:download_attachment', args=(a.pk,))),
            )

    def __init__(self, *args, **kwargs):
        self.attached_to = kwargs.pop(u'attached_to')
        super(AttachmentsMixin, self).__init__(*args, **kwargs)

        self.fields[u'attachments'].attached_to = self.attached_to

    def save(self, action):
        super(AttachmentsMixin, self).save(action)

        @after_saved(action)
        def deferred():
            action.attachment_set = self.cleaned_data[u'attachments']

    def save_to_draft(self, draft):
        super(AttachmentsMixin, self).save_to_draft(draft)

        @after_saved(draft)
        def deferred():
            draft.attachment_set = self.cleaned_data[u'attachments']

    def load_from_draft(self, draft):
        super(AttachmentsMixin, self).load_from_draft(draft)
        self.initial[u'attachments'] = draft.attachment_set.all()

class DeadlineMixin(ActionAbstractForm):
    deadline = forms.IntegerField(
            label=_(u'New Deadline'),
            initial=Action.DEFAULT_DEADLINES.EXTENSION,
            min_value=2,
            max_value=100,
            widget=forms.NumberInput(attrs={
                u'placeholder': _(u'Deadline'),
                }),
            )

    def __init__(self, *args, **kwargs):
        super(DeadlineMixin, self).__init__(*args, **kwargs)
        if self.draft:
            self.fields[u'deadline'].required = False

    def save(self, action):
        super(DeadlineMixin, self).save(action)
        action.deadline = self.cleaned_data[u'deadline']

    def save_to_draft(self, draft):
        super(DeadlineMixin, self).save_to_draft(draft)
        draft.deadline = self.cleaned_data[u'deadline']

    def load_from_draft(self, draft):
        super(DeadlineMixin, self).load_from_draft(draft)
        self.initial[u'deadline'] = draft.deadline

class AdvancedToMixin(ActionAbstractForm):
    advanced_to_1 = ObligeeAutocompleteField(
            label=_(u'Advanced To'),
            widget=ObligeeWithAddressInput(attrs={
                u'placeholder': _(u'Obligee'),
                }),
            )
    advanced_to_2 = ObligeeAutocompleteField(
            label=u'',
            required=False,
            widget=ObligeeWithAddressInput(attrs={
                u'placeholder': _(u'Obligee'),
                }),
            )
    advanced_to_3 = ObligeeAutocompleteField(
            label=u'',
            required=False,
            widget=ObligeeWithAddressInput(attrs={
                u'placeholder': _(u'Obligee'),
                }),
            )
    ADVANCED_TO_FIELDS = [u'advanced_to_1', u'advanced_to_2', u'advanced_to_3']

    def __init__(self, *args, **kwargs):
        super(AdvancedToMixin, self).__init__(*args, **kwargs)
        if self.draft:
            for field in self.ADVANCED_TO_FIELDS:
                self.fields[field].required = False

    def clean(self):
        cleaned_data = super(AdvancedToMixin, self).clean()

        if not self.draft:
            paperwork = cleaned_data.get(u'paperwork', None)
            for i, field in enumerate(self.ADVANCED_TO_FIELDS):
                advanced_to = cleaned_data.get(field, None)
                if advanced_to:
                    try:
                        if paperwork and advanced_to == paperwork.obligee:
                            raise ValidationError(_(u'May not advance to the same obligee.'))
                        for field_2 in self.ADVANCED_TO_FIELDS[0:i]:
                            advanced_to_2 = cleaned_data.get(field_2, None)
                            if advanced_to_2 == advanced_to:
                                raise ValidationError(_(u'May not advance twice to the same obligee.'))
                    except ValidationError as e:
                        self._errors[field] = self.error_class(e.messages)
                        del cleaned_data[field]

        return cleaned_data

    def save(self, action):
        super(AdvancedToMixin, self).save(action)

        @after_saved(action)
        def deferred():
            for field in self.ADVANCED_TO_FIELDS:
                obligee = self.cleaned_data[field]
                if obligee:
                    sub_paperwork = Paperwork(
                            obligee=obligee,
                            inforequest=action.paperwork.inforequest,
                            advanced_by=action,
                            )
                    sub_paperwork.save()

                    sub_action = Action(
                            paperwork=sub_paperwork,
                            effective_date=action.effective_date,
                            type=Action.TYPES.ADVANCED_REQUEST,
                            )
                    sub_action.save()

    def save_to_draft(self, draft):
        super(AdvancedToMixin, self).save_to_draft(draft)

        @after_saved(draft)
        def deferred():
            draft.obligee_set = [self.cleaned_data[f]
                    for f in self.ADVANCED_TO_FIELDS
                    if self.cleaned_data[f]]

    def load_from_draft(self, draft):
        super(AdvancedToMixin, self).load_from_draft(draft)
        for field, obligee in zip(self.ADVANCED_TO_FIELDS, draft.obligee_set.all()):
            self.initial[field] = obligee

class DisclosureLevelMixin(ActionAbstractForm):
    disclosure_level = forms.TypedChoiceField(
            label=_(u'Disclosure Level'),
            choices=[(u'', u'')] + Action.DISCLOSURE_LEVELS._choices,
            coerce=int,
            empty_value=None,
            )

    def __init__(self, *args, **kwargs):
        super(DisclosureLevelMixin, self).__init__(*args, **kwargs)
        if self.draft:
            self.fields[u'disclosure_level'].required = False

    def save(self, action):
        super(DisclosureLevelMixin, self).save(action)
        action.disclosure_level = self.cleaned_data[u'disclosure_level']

    def save_to_draft(self, draft):
        super(DisclosureLevelMixin, self).save_to_draft(draft)
        draft.disclosure_level = self.cleaned_data[u'disclosure_level'] if self.cleaned_data[u'disclosure_level'] != u'' else None

    def load_from_draft(self, draft):
        super(DisclosureLevelMixin, self).load_from_draft(draft)
        self.initial[u'disclosure_level'] = draft.disclosure_level

class RefusalReasonMixin(ActionAbstractForm):
    refusal_reason = forms.TypedChoiceField(
            label=_(u'Refusal Reason'),
            choices=[(u'', u'')] + Action.REFUSAL_REASONS._choices,
            coerce=int,
            empty_value=None,
            )

    def __init__(self, *args, **kwargs):
        super(RefusalReasonMixin, self).__init__(*args, **kwargs)
        if self.draft:
            self.fields[u'refusal_reason'].required = False

    def save(self, action):
        super(RefusalReasonMixin, self).save(action)
        action.refusal_reason = self.cleaned_data[u'refusal_reason']

    def save_to_draft(self, draft):
        super(RefusalReasonMixin, self).save_to_draft(draft)
        draft.refusal_reason = self.cleaned_data[u'refusal_reason'] if self.cleaned_data[u'refusal_reason'] != u'' else None

    def load_from_draft(self, draft):
        super(RefusalReasonMixin, self).load_from_draft(draft)
        self.initial[u'refusal_reason'] = draft.refusal_reason


class DecideEmailCommonForm(ActionAbstractForm):
    pass

class ConfirmationEmailForm(DecideEmailCommonForm):
    pass

class ExtensionEmailForm(DecideEmailCommonForm, DeadlineMixin):
    pass

class AdvancementEmailForm(DecideEmailCommonForm, DisclosureLevelMixin, AdvancedToMixin):
    pass

class ClarificationRequestEmailForm(DecideEmailCommonForm):
    pass

class DisclosureEmailForm(DecideEmailCommonForm, DisclosureLevelMixin):
    pass

class RefusalEmailForm(DecideEmailCommonForm, RefusalReasonMixin):
    pass


class AddSmailCommonForm(EffectiveDateMixin, SubjectContentMixin, AttachmentsMixin, ActionAbstractForm):
    def clean(self):
        cleaned_data = super(AddSmailCommonForm, self).clean()

        if not self.draft:
            if self.inforequest.has_undecided_email:
                msg = squeeze(render_to_string(u'inforequests/messages/add_smail-undecided_emails.txt', {
                        u'inforequest': self.inforequest,
                        }))
                raise forms.ValidationError(msg, code=u'undecided_emails')

        return cleaned_data

class ConfirmationSmailForm(AddSmailCommonForm):
    pass

class ExtensionSmailForm(AddSmailCommonForm, DeadlineMixin):
    pass

class AdvancementSmailForm(AddSmailCommonForm, DisclosureLevelMixin, AdvancedToMixin):
    pass

class ClarificationRequestSmailForm(AddSmailCommonForm):
    pass

class DisclosureSmailForm(AddSmailCommonForm, DisclosureLevelMixin):
    pass

class RefusalSmailForm(AddSmailCommonForm, RefusalReasonMixin):
    pass

class AffirmationSmailForm(AddSmailCommonForm, RefusalReasonMixin):
    pass

class ReversionSmailForm(AddSmailCommonForm, DisclosureLevelMixin):
    pass

class RemandmentSmailForm(AddSmailCommonForm, DisclosureLevelMixin):
    pass


class NewActionCommonForm(SubjectContentMixin, AttachmentsMixin, ActionAbstractForm):
    def clean(self):
        cleaned_data = super(NewActionCommonForm, self).clean()

        if not self.draft:
            if self.inforequest.has_undecided_email:
                msg = squeeze(render_to_string(u'inforequests/messages/new_action-undecided_emails.txt', {
                        u'inforequest': self.inforequest,
                        }))
                raise forms.ValidationError(msg, code=u'undecided_emails')

        return cleaned_data

class ClarificationResponseForm(NewActionCommonForm):
    pass

class AppealForm(NewActionCommonForm):
    pass


class ExtendDeadlineForm(PrefixedForm):
    extension = forms.IntegerField(
            label=_(u'Deadline Extension'),
            initial=5,
            min_value=2,
            max_value=100,
            widget=forms.NumberInput(attrs={
                u'placeholder': _(u'Working Days'),
                }),
            )

    def save(self, action):
        if not self.is_valid():
            raise ValueError

        # User sets the extended deadline relative to today.
        if action.deadline is not None:
            action.extension = action.days_passed - action.deadline + self.cleaned_data[u'extension']
