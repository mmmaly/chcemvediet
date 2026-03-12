# vim: expandtab
# -*- coding: utf-8 -*-
from collections import defaultdict

from django import forms
from django.core.exceptions import ValidationError
from django.utils.translation import gettext_lazy as _
from multiselectfield import MultiSelectFormField

from chcemvediet.apps.inforequests.models import Action


class BranchField(forms.TypedChoiceField):

    def __init__(self, *args, **kwargs):
        inforequest = kwargs.pop(u'inforequest', None)
        super(BranchField, self).__init__(coerce=self.coerce, empty_value=None, *args, **kwargs)
        self.inforequest = inforequest

    @property
    def inforequest(self):
        return self._inforequest

    @inforequest.setter
    def inforequest(self, inforequest):
        self._inforequest = inforequest

        # Branches tree structure
        choices = [(None, u'')]
        tree = defaultdict(list)
        for branch in inforequest.branches:
            parent = None if branch.is_main else branch.advanced_by.branch
            tree[parent].append(branch)
        stack = [(0, b) for b in tree[None][::-1]]
        while stack:
            level, branch = stack.pop()
            prefix = u'  '*(level-1) + u' - ' if level > 0 else u''
            choices.append((branch.pk, prefix + branch.historicalobligee.name))
            stack.extend((level+1, b) for b in tree[branch][::-1])
        self.choices = choices

    def coerce(self, value):
        value = int(value)
        for branch in self.inforequest.branches:
            if value == branch.pk:
                return branch
        raise ValueError

class RefusalReasonField(MultiSelectFormField):

    def __init__(self, *args, **kwargs):
        self.allow_no_reason = kwargs.pop(u'allow_no_reason', True)
        self.section_3 = kwargs.pop(u'section_3', False)
        kwargs.setdefault(u'label', u' ')

        choices = kwargs.pop(u'choices', Action.REFUSAL_REASONS._choices)
        if not self.section_3:
            # Only obligees defined in section 3 (of §2) may refuse to disclose information saying
            # they are not obliged to provide such information.
            choices = [(k, v) for k, v in choices if k != Action.REFUSAL_REASONS.DOES_NOT_PROVIDE]
        if self.allow_no_reason:
            choices = choices + [(u'none', _(u'inforequests:RefusalReasonField:no_reason'))]

        super(RefusalReasonField, self).__init__(choices=choices, *args, **kwargs)

    def clean(self, value):
        value = super(RefusalReasonField, self).clean(value)
        if value == [u'none']:
            return []
        if u'none' in value:
            raise ValidationError(_(u'inforequests:RefusalReasonField:error:none_contradiction'))
        return value
