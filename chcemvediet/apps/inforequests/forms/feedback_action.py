# vim: expandtab
# -*- coding: utf-8 -*-

from django import forms
from django.utils.translation import gettext_lazy as _

from chcemvediet.apps.inforequests.models import Feedback
from poleno.utils.urls import reverse
from chcemvediet.apps.wizards.wizard import Bottom, Step, Wizard


class FeedbackActionStep(Step):
    template = u'inforequests/feedback_action/wizard.html'
    form_template = u'main/forms/form_horizontal.html'


class FeedbackContent(FeedbackActionStep):
    label = u'label free text feedback'
    text_template = u'inforequests/feedback_action/texts/content.html'
    global_fields = [u'content']
    post_step_class = Bottom

    def add_fields(self):
        super(FeedbackContent, self).add_fields()

        self.fields[u'content'] = forms.CharField(
            label=_(u'inforequests:feedback_action:FeedbackContent:content:label'),
            required=False,
            widget=forms.Textarea(attrs={
                u'placeholder':
                    _(u'inforequests:feedback_action:FeedbackContent:content:placeholder'),
                u'class': u'pln-autosize',
                u'cols': u'', u'rows': u''
            })
        )


class FeedbackRating(FeedbackActionStep):
    label = u''
    text_template = u'inforequests/feedback_action/texts/rating.html'
    global_fields = [u'rating']
    post_step_class = FeedbackContent

    def add_fields(self):
        super(FeedbackRating, self).add_fields()
        self.fields[u'rating'] = forms.TypedChoiceField(
            label=u' ',
            coerce=int,
            choices=Feedback.RATING_LEVELS._choices,
            widget=forms.RadioSelect(),
        )


class FeedbackActionWizard(Wizard):
    first_step_class = FeedbackRating

    def __init__(self, request, index, inforequest):
        self.inforequest = inforequest
        super(FeedbackActionWizard, self).__init__(request, index)

    def get_instance_id(self):
        return u'{}-{}'.format(self.__class__.__name__, self.inforequest.pk)

    def get_step_url(self, step, anchor=u''):
        return reverse(u'inforequests:feedback_action',
                       kwargs=dict(inforequest=self.inforequest, step=step)) + anchor

    def context(self, extra=None):
        res = super(FeedbackActionWizard, self).context(extra)
        res.update({
            u'inforequest': self.inforequest
        })
        return res

    def finish(self):
        feedback = Feedback(
            inforequest=self.inforequest,
            content=self.values[u'content'],
            rating=self.values[u'rating']
        )
        feedback.save()

        return self.inforequest.get_absolute_url()
