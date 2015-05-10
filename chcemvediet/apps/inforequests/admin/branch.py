# vim: expandtab
# -*- coding: utf-8 -*-
from django import forms
from django.core.exceptions import ValidationError
from django.contrib import admin
from django.contrib.admin.templatetags.admin_list import _boolean_icon

from poleno.utils.models import after_saved
from poleno.utils.misc import decorate
from poleno.utils.admin import (simple_list_filter_factory, admin_obj_format, live_field,
        AdminLiveFieldsMixin, ADMIN_FIELD_INDENT)

from chcemvediet.apps.inforequests.models import Branch, Action


class BranchAdminActionInline(admin.TabularInline):
    model = Action
    extra = 0
    template = u'admin/inforequests/branch/action_inline.html'

    fields = [
            u'action_field',
            u'email_field',
            u'type',
            u'effective_date',
            u'deadline_details_field',
            ]
    readonly_fields = fields
    ordering = [u'pk']

    @decorate(short_description=u'Action')
    def action_field(self, action):
        return admin_obj_format(action)

    @decorate(short_description=u'E-mail')
    def email_field(self, action):
        email = action.email
        return admin_obj_format(email)

    @decorate(short_description=u'Deadline')
    def deadline_details_field(self, action):
        if action.has_applicant_deadline:
            if action.deadline_missed:
                return u'Applicant deadline was missed {days} working days ago.'.format(days=-action.deadline_remaining)
            else:
                return u'Applicant deadline will be missed in {days} working days.'.format(days=action.deadline_remaining)
        elif action.has_obligee_deadline:
            if action.deadline_missed:
                return u'Obligee deadline was missed {days} working days ago.'.format(days=-action.deadline_remaining)
            else:
                return u'Obligee deadline will be missed in {days} working days.'.format(days=action.deadline_remaining)
        else:
            return u'Action has no deadline.'

    def has_add_permission(self, request):
        return False

    def has_delete_permission(self, request, obj=None):
        return False

    def get_queryset(self, request):
        queryset = super(BranchAdminActionInline, self).get_queryset(request)
        queryset = queryset.select_related(u'email')
        return queryset

class BranchAdminAddForm(forms.ModelForm):
    def __init__(self, *args, **kwargs):
        super(BranchAdminAddForm, self).__init__(*args, **kwargs)
        self.fields[u'advanced_by'].required = True

    def save(self, commit=True):
        assert self.is_valid()

        branch = Branch(
                inforequest=self.cleaned_data[u'advanced_by'].branch.inforequest,
                obligee=self.cleaned_data[u'obligee'],
                advanced_by=self.cleaned_data[u'advanced_by'],
                )

        @after_saved(branch)
        def deferred(branch):
            action = Action(
                    branch=branch,
                    effective_date=self.cleaned_data[u'advanced_by'].effective_date,
                    type=Action.TYPES.ADVANCED_REQUEST,
                    )
            action.save()

        if commit:
            branch.save()
        return branch

    def save_m2m(self):
        pass

class BranchAdminChangeForm(forms.ModelForm):
    def clean(self):
        cleaned_data = super(BranchAdminChangeForm, self).clean()

        if u'advanced_by' in cleaned_data:
            advanced_by = cleaned_data[u'advanced_by']
            try:
                if self.instance.advanced_by is None and advanced_by is not None:
                    raise ValidationError(u'This field must be empty for main branches.')
                if self.instance.advanced_by is not None and advanced_by is None:
                    raise ValidationError(u'This field is required for advanced branches.')

                if u'inforequest' in cleaned_data:
                    inforequest = cleaned_data[u'inforequest']
                    if advanced_by is not None and inforequest.pk != advanced_by.branch.inforequest_id:
                        raise ValidationError(u'Advanced branch must belong to the same inforequest as the parent branch.')

                node = advanced_by
                count = 0
                while node is not None:
                    if node.branch_id == self.instance.pk:
                        raise ValidationError(u'The branch may not be a sub-branch of itself.')
                    if count > 10:
                        raise ValidationError(u'Too deep branch inheritance.')
                    node = node.branch.advanced_by
                    count += 1

            except ValidationError as e:
                self.add_error(u'advanced_by', e)

        return cleaned_data

class BranchAdmin(AdminLiveFieldsMixin, admin.ModelAdmin):
    list_display = [
            u'branch_column',
            u'inforequest_column',
            u'inforequest_closed_column',
            u'inforequest_applicant_column',
            u'obligee_column',
            u'main_branch_column',
            ]
    list_filter = [
            simple_list_filter_factory(u'Main Branch', u'mainbranch', [
                (u'1', u'Yes', lambda qs: qs.main()),
                (u'0', u'No',  lambda qs: qs.advanced()),
                ]),
            u'inforequest__closed',
            ]
    search_fields = [
            u'=id',
            u'=inforequest__pk',
            u'inforequest__applicant__first_name',
            u'inforequest__applicant__last_name',
            u'inforequest__applicant__email',
            u'obligee__name',
            ]
    ordering = [u'-pk']

    @decorate(short_description=u'Branch')
    @decorate(admin_order_field=u'pk')
    def branch_column(self, branch):
        return admin_obj_format(branch, link=False)

    @decorate(short_description=u'Inforequest')
    @decorate(admin_order_field=u'inforequest__pk')
    def inforequest_column(self, branch):
        inforequest = branch.inforequest
        return admin_obj_format(inforequest)

    @decorate(short_description=u'Closed')
    @decorate(admin_order_field=u'inforequest__closed')
    @decorate(boolean=True)
    def inforequest_closed_column(self, inforequestemail):
        return inforequestemail.inforequest.closed

    @decorate(short_description=u'Applicant')
    @decorate(admin_order_field=u'inforequest__applicant__email')
    def inforequest_applicant_column(self, branch):
        user = branch.inforequest.applicant
        return admin_obj_format(user, u'{obj.first_name} {obj.last_name} <{obj.email}>')

    @decorate(short_description=u'Obligee')
    @decorate(admin_order_field=u'obligee__name')
    def obligee_column(self, branch):
        obligee = branch.obligee
        return admin_obj_format(obligee, u'{obj.name}')

    @decorate(short_description=u'Main Branch')
    @decorate(admin_order_field=u'advanced_by')
    @decorate(boolean=True)
    def main_branch_column(self, branch):
        return branch.is_main

    form_add = BranchAdminAddForm
    form_change = BranchAdminChangeForm
    fieldsets = [
            (None, {
                u'classes': [u'wide'],
                u'fields': [
                    u'inforequest',
                    u'obligee',
                    u'obligee_details_live',
                    u'historicalobligee',
                    u'historicalobligee_details_live',
                    u'advanced_by',
                    u'advanced_by_details_live',
                    u'advanced_by_branch_live',
                    u'advanced_by_inforequest_live',
                    u'advanced_by_applicant_live',
                    u'advanced_by_closed_live',
                    ],
                }),
            ]
    fieldsets_add = [
            (None, {
                u'classes': [u'wide'],
                u'fields': [
                    u'obligee',
                    u'obligee_details_live',
                    u'advanced_by',
                    u'advanced_by_details_live',
                    u'advanced_by_branch_live',
                    u'advanced_by_inforequest_live',
                    u'advanced_by_applicant_live',
                    u'advanced_by_closed_live',
                    ],
                }),
            ]
    raw_id_fields = [
            u'inforequest',
            u'obligee',
            u'historicalobligee',
            u'advanced_by',
            ]
    live_fields = [
            u'obligee_details_live',
            u'historicalobligee_details_live',
            u'advanced_by_details_live',
            u'advanced_by_branch_live',
            u'advanced_by_inforequest_live',
            u'advanced_by_applicant_live',
            u'advanced_by_closed_live',
            ]
    readonly_fields = live_fields
    inlines = [
            BranchAdminActionInline,
            ]

    @decorate(short_description=u'%s%s' % (ADMIN_FIELD_INDENT, u'Details'))
    @live_field(u'obligee')
    def obligee_details_live(self, obligee):
        return admin_obj_format(obligee, u'{tag}\n{obj.name}')

    @decorate(short_description=u'%s%s' % (ADMIN_FIELD_INDENT, u'Details'))
    @live_field(u'historicalobligee')
    def historicalobligee_details_live(self, historicalobligee):
        return admin_obj_format(historicalobligee, u'{tag}\n{obj.name}')

    @decorate(short_description=u'%s%s' % (ADMIN_FIELD_INDENT, u'Details'))
    @live_field(u'advanced_by')
    def advanced_by_details_live(self, advanced_by):
        action = advanced_by
        return admin_obj_format(action, u'{tag} {0}', action.get_type_display()) if action else u'--'

    @decorate(short_description=u'%s%s' % (ADMIN_FIELD_INDENT, u'Branch'))
    @live_field(u'advanced_by')
    def advanced_by_branch_live(self, advanced_by):
        branch = advanced_by.branch if advanced_by else None
        return admin_obj_format(branch)

    @decorate(short_description=u'%s%s' % (ADMIN_FIELD_INDENT, u'Inforequest'))
    @live_field(u'advanced_by')
    def advanced_by_inforequest_live(self, advanced_by):
        inforequest = advanced_by.branch.inforequest if advanced_by else None
        return admin_obj_format(inforequest)

    @decorate(short_description=u'%s%s' % (ADMIN_FIELD_INDENT, u'Applicant'))
    @live_field(u'advanced_by')
    def advanced_by_applicant_live(self, advanced_by):
        user = advanced_by.branch.inforequest.applicant if advanced_by else None
        return admin_obj_format(user, u'{tag}\n{obj.first_name} {obj.last_name} <{obj.email}>')

    @decorate(short_description=u'%s%s' % (ADMIN_FIELD_INDENT, u'Closed'))
    @live_field(u'advanced_by')
    def advanced_by_closed_live(self, advanced_by):
        return _boolean_icon(advanced_by.branch.inforequest.closed) if advanced_by else u'--'

    def has_delete_permission(self, request, obj=None):
        if not obj:
            return True
        # Only advanced branches may be deleted. If we want to delete a main branch, we must delete
        # its inforequest.
        return not obj.is_main

    def get_queryset(self, request):
        queryset = super(BranchAdmin, self).get_queryset(request)
        queryset = queryset.select_related(u'inforequest__applicant')
        queryset = queryset.select_related(u'obligee')
        return queryset

    def get_fieldsets(self, request, obj=None):
        if obj is None:
            return self.fieldsets_add
        return super(BranchAdmin, self).get_fieldsets(request, obj)

    def get_form(self, request, obj=None, **kwargs):
        if obj is None:
            self.form = self.form_add
            form = super(BranchAdmin, self).get_form(request, obj, **kwargs)
        else:
            self.form = self.form_change
            form = super(BranchAdmin, self).get_form(request, obj, **kwargs)
        return form

    def get_formsets(self, request, obj=None):
        if obj is None:
            return []
        return super(BranchAdmin, self).get_formsets(request, obj)

admin.site.register(Branch, BranchAdmin)
