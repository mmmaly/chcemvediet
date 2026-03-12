# vim: expandtab
# -*- coding: utf-8 -*-
from dateutil.relativedelta import relativedelta

from django import forms
from django.core.exceptions import ValidationError
from django.utils.translation import gettext_lazy as _

from poleno.utils.date import local_today
from poleno.utils.misc import squeeze
from chcemvediet.apps.wizards.wizard import Step, SectionStep, DeadendStep, PaperStep, PrintStep


class AppealStep(Step):
    template = u'inforequests/appeal/wizard.html'

class AppealSectionStep(AppealStep, SectionStep):
    pass

class AppealDeadendStep(AppealStep, DeadendStep):
    pass

class AppealFinalStep(AppealStep, PrintStep):
    label = _(u'inforequests:appeal:AppealFinalStep:label')
    text_template = u'inforequests/appeal/texts/final.html'

    def clean(self):
        cleaned_data = super(AppealFinalStep, self).clean()

        if self.wizard.inforequest.has_undecided_emails:
            msg = _(u'inforequests:appeal:AppealFinalStep:error:undecided_emails')
            self.add_error(None, msg)

        return cleaned_data

    def context(self, extra=None):
        res = super(AppealFinalStep, self).context(extra)

        last_action = self.wizard.last_action
        legal_date = self.wizard.values[u'legal_date']
        if last_action.has_applicant_deadline:
            res.update({
                    u'is_deadline_missed_at_today':
                        last_action.deadline.is_deadline_missed,
                    u'calendar_days_behind_at_today':
                        last_action.deadline.calendar_days_behind,
                    u'is_deadline_missed_at_legal_date':
                        last_action.deadline.is_deadline_missed_at(legal_date),
                    u'calendar_days_behind_at_legal_date':
                        last_action.deadline.calendar_days_behind_at(legal_date),
                    })

        return res

class AppealPaperStep(AppealStep, PaperStep):
    subject_template = u'inforequests/appeal/papers/subject.txt'
    content_template = u'inforequests/appeal/papers/content.html'
    pre_step_class = AppealFinalStep

class AppealLegalDateStep(AppealStep):
    label = _(u'inforequests:appeal:AppealLegalDateStep:label')
    text_template = u'inforequests/appeal/texts/legal_date.html'
    form_template = u'main/forms/form_horizontal.html'
    global_fields = [u'legal_date']
    post_step_class = AppealPaperStep

    def add_fields(self):
        super(AppealLegalDateStep, self).add_fields()

        self.fields[u'legal_date'] = forms.DateField(
                label=_(u'inforequests:appeal:AppealLegalDateStep:legal_date:label'),
                localize=True,
                initial=local_today,
                widget=forms.DateInput(attrs={
                    u'placeholder': _('inforequests:appeal:AppealLegalDateStep:legal_date:placeholder'),
                    u'class': u'pln-datepicker',
                    }),
                )

    def clean(self):
        cleaned_data = super(AppealLegalDateStep, self).clean()

        branch = self.wizard.branch
        legal_date = cleaned_data.get(u'legal_date', None)
        if legal_date is not None:
            try:
                if legal_date < branch.last_action.legal_date:
                    msg = _(u'inforequests:appeal:AppealLegalDateStep:legal_date:error:older_than_last_action')
                    raise ValidationError(msg)
                if legal_date < local_today():
                    msg = _(u'inforequests:appeal:AppealLegalDateStep:legal_date:error:from_past')
                    raise ValidationError(msg)
                if legal_date > local_today() + relativedelta(days=5):
                    msg = _(u'inforequests:appeal:AppealLegalDateStep:legal_date:error:too_far_from_future')
                    raise ValidationError(msg)
            except ValidationError as e:
                if u'legal_date' in cleaned_data:
                    self.add_error(u'legal_date', e)

        return cleaned_data
