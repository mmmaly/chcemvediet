# vim: expandtab
# -*- coding: utf-8 -*-
from django import forms
from django.utils.translation import ugettext_lazy as _, pgettext_lazy
from django.contrib.webdesign.lorem_ipsum import paragraphs as lorem

from poleno.utils.model import after_saved
from poleno.utils.form import AutoSuppressedSelect
from chcemvediet.apps.obligees.forms import ObligeeWithAddressInput, ObligeeAutocompleteField

from models import History, Action


class HistoryChoiceField(forms.ModelChoiceField):
    def label_from_instance(self, history):
        return history.obligee_name;


class InforequestForm(forms.Form):
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

    def save(self, inforequest):
        if not self.is_valid():
            raise ValueError(u"The %s could not be saved because the data didn't validate." % type(self).__name__)

        @after_saved(inforequest)
        def deferred():
            history = History(
                    obligee=self.cleaned_data[u'obligee'],
                    inforequest=inforequest,
                    )
            history.save()

            action = Action(
                    history=history,
                    subject=self.cleaned_data[u'subject'],
                    content=self.cleaned_data[u'content'],
                    effective_date=inforequest.submission_date,
                    type=Action.TYPES.REQUEST,
                    )
            action.save()

class InforequestDraftForm(InforequestForm):

    def __init__(self, *args, **kwargs):
        super(InforequestDraftForm, self).__init__(*args, **kwargs)
        self.fields[u'obligee'].required = False
        self.fields[u'subject'].required = False
        self.fields[u'content'].required = False

    def save(self, draft):
        if not self.is_valid():
            raise ValueError(u"The %s could not be saved because the data didn't validate." % type(self).__name__)

        draft.obligee = self.cleaned_data[u'obligee']
        draft.subject = self.cleaned_data[u'subject']
        draft.content = self.cleaned_data[u'content']

    def load(self, draft):
        self.initial[u'obligee'] = draft.obligee
        self.initial[u'subject'] = draft.subject
        self.initial[u'content'] = draft.content


class ActionAbstractForm(forms.Form):
    history = HistoryChoiceField(
            queryset=History.objects.none(),
            label=_(u'Obligee'),
            empty_label=u'',
            widget=AutoSuppressedSelect(suppressed_attrs={
                u'class': u'suppressed-control',
                }),
            )

    def __init__(self, *args, **kwargs):
        history_set = kwargs.pop(u'history_set')
        super(ActionAbstractForm, self).__init__(*args, **kwargs)

        field = self.fields[u'history']
        field.queryset = history_set
        if history_set.count() == 1:
            field.empty_label = None

        if not self.prefix:
            self.prefix = self.__class__.__name__.lower()

    def save(self, action):
        if not self.is_valid():
            raise ValueError(u"The %s could not be saved because the data didn't validate." % type(self).__name__)

        action.history = self.cleaned_data[u'history']

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

    def save(self, action):
        super(DeadlineMixin, self).save(action)
        action.deadline = self.cleaned_data[u'deadline']

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

    def save(self, action):
        super(AdvancedToMixin, self).save(action)

        @after_saved(action)
        def deferred():
            for field in [u'advanced_to_1', u'advanced_to_2', u'advanced_to_3']:
                obligee = self.cleaned_data[field]
                if obligee:
                    sub_history = History(
                            obligee=obligee,
                            inforequest=action.history.inforequest,
                            advanced_by=action,
                            )
                    sub_history.save()

                    sub_action = Action(
                            history=sub_history,
                            effective_date=action.effective_date,
                            type=Action.TYPES.ADVANCED_REQUEST,
                            )
                    sub_action.save()

class DisclosureLevelMixin(ActionAbstractForm):
    disclosure_level = forms.ChoiceField(
            label=_(u'Disclosure Level'),
            choices=[(u'', u'')] + Action.DISCLOSURE_LEVELS._choices,
            )

    def save(self, action):
        super(DisclosureLevelMixin, self).save(action)
        action.disclosure_level = self.cleaned_data[u'disclosure_level']

class RefusalReasonMixin(ActionAbstractForm):
    refusal_reason = forms.ChoiceField(
            label=_(u'Refusal Reason'),
            choices=[(u'', u'')] + Action.REFUSAL_REASONS._choices,
            )

    def save(self, action):
        super(RefusalReasonMixin, self).save(action)
        action.refusal_reason = self.cleaned_data[u'refusal_reason']


class DecideEmailCommonForm(ActionAbstractForm):
    pass

class ConfirmationEmailForm(DecideEmailCommonForm):
    pass

class ExtensionEmailForm(DecideEmailCommonForm, DeadlineMixin):
    pass

class AdvancementEmailForm(DecideEmailCommonForm, AdvancedToMixin):
    pass

class ClarificationRequestEmailForm(DecideEmailCommonForm):
    pass

class DisclosureEmailForm(DecideEmailCommonForm, DisclosureLevelMixin):
    pass

class RefusalEmailForm(DecideEmailCommonForm, RefusalReasonMixin):
    pass


class AddSmailCommonForm(ActionAbstractForm):
    effective_date = forms.DateField(
            label=_(u'Effective Date'),
            localize=True,
            widget=forms.DateInput(attrs={
                u'placeholder': pgettext_lazy(u'Form Date Placeholder', u'mm/dd/yyyy'),
                u'class': u'datepicker',
                }),
            )
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

    def save(self, action):
        super(AddSmailCommonForm, self).save(action)
        action.effective_date = self.cleaned_data[u'effective_date']
        action.subject = self.cleaned_data[u'subject']
        action.content = self.cleaned_data[u'content']

class ConfirmationSmailForm(AddSmailCommonForm):
    pass

class ExtensionSmailForm(AddSmailCommonForm, DeadlineMixin):
    pass

class AdvancementSmailForm(AddSmailCommonForm, AdvancedToMixin):
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
