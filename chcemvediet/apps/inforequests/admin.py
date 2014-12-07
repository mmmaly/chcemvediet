# vim: expandtab
# -*- coding: utf-8 -*-
from django import forms
from django.db.models import Q
from django.utils.translation import ugettext_lazy as _
from django.contrib import admin
from django.contrib.auth.models import User
from aggregate_if import Count

from poleno.attachments.models import Attachment
from poleno.attachments.admin import AttachmentInline
from poleno.mail.models import Message
from poleno.utils.models import after_saved
from poleno.utils.misc import decorate, squeeze
from poleno.utils.admin import simple_list_filter_factory, admin_obj_link, extend_model_admin

from .models import InforequestDraft, Inforequest, InforequestEmail, Branch, Action, ActionDraft


ADMIN_FIELD_INDENT = u'    • '

def action_deadline_details(action):
    if action.has_applicant_deadline:
        if action.deadline_missed:
            return _(u'Applicant deadline was missed {days} working days ago.').format(days=-action.deadline_remaining)
        else:
            return _(u'Applicant deadline will be missed in {days} working days.').format(days=action.deadline_remaining)
    elif action.has_obligee_deadline:
        if action.deadline_missed:
            return _(u'Obligee deadline was missed {days} working days ago.').format(days=-action.deadline_remaining)
        else:
            return _(u'Obligee deadline will be missed in {days} working days.').format(days=action.deadline_remaining)
    else:
        return _(u'Action has no deadline.')


class InforequestDraftAdminAddForm(forms.Form):
    applicant = InforequestDraft._meta.get_field(u'applicant').formfield(
            widget=admin.widgets.ForeignKeyRawIdWidget(
                InforequestDraft._meta.get_field(u'applicant').rel, admin.site),
            )
    obligee = InforequestDraft._meta.get_field(u'obligee').formfield(
            widget=admin.widgets.ForeignKeyRawIdWidget(
                InforequestDraft._meta.get_field(u'obligee').rel, admin.site),
            )
    subject = InforequestDraft._meta.get_field(u'subject').formfield(
            widget=admin.widgets.AdminTextInputWidget(),
            )
    content = InforequestDraft._meta.get_field(u'content').formfield(
            widget=admin.widgets.AdminTextareaWidget(),
            )
    # FIXME: attachments

    def save(self, commit=True):
        # Django admin runs it with commit=False only
        assert commit is False
        assert self.is_valid()

        draft = InforequestDraft(
                applicant=self.cleaned_data[u'applicant'],
                obligee=self.cleaned_data[u'obligee'],
                subject=self.cleaned_data[u'subject'],
                content=self.cleaned_data[u'content'],
                )

        return draft

    def save_m2m(self):
        pass

class InforequestDraftAdmin(admin.ModelAdmin):
    list_display = [
            u'inforequestdraft_column',
            u'applicant_column',
            u'obligee_column',
            ]
    list_filter = [
            ]
    search_fields = [
            u'=id',
            u'applicant__first_name',
            u'applicant__last_name',
            u'applicant__email',
            u'obligee__name',
            ]

    @decorate(short_description=_(u'Inforequest Draft'))
    @decorate(admin_order_field=u'pk')
    def inforequestdraft_column(self, draft):
        return u'<%s: %s>' % (draft.__class__.__name__, draft.pk)

    @decorate(short_description=_(u'Applicant'))
    @decorate(admin_order_field=u'applicant__email')
    @decorate(allow_tags=True)
    def applicant_column(self, draft):
        user = draft.applicant
        return admin_obj_link(user, u'%s <%s>' % (user.get_full_name(), user.email))

    @decorate(short_description=_(u'Obligee'))
    @decorate(admin_order_field=u'obligee')
    @decorate(allow_tags=True)
    def obligee_column(self, draft):
        obligee = draft.obligee
        return admin_obj_link(obligee, obligee.name) if obligee else u'--'

    fieldsets = [
            (None, {
                u'fields': [
                    u'applicant',
                    u'applicant_details_field',
                    u'obligee',
                    u'obligee_details_field',
                    u'subject',
                    u'content',
                    ],
                }),
            ]
    fieldsets_add = [
            (None, {
                u'fields': [
                    u'applicant',
                    u'obligee',
                    u'subject',
                    u'content',
                    ],
                }),
            ]
    readonly_fields = [
            u'applicant_details_field',
            u'obligee_details_field',
            ]
    raw_id_fields = [
            u'applicant',
            u'obligee',
            ]
    inlines = [
            AttachmentInline,
            ]

    @decorate(short_description=u'%s%s' % (ADMIN_FIELD_INDENT, _(u'Details')))
    @decorate(allow_tags=True)
    def applicant_details_field(self, draft):
        user = draft.applicant
        return admin_obj_link(user, u'\n%s <%s>' % (user.get_full_name(), user.email), show_pk=True)

    @decorate(short_description=u'%s%s' % (ADMIN_FIELD_INDENT, _(u'Details')))
    @decorate(allow_tags=True)
    def obligee_details_field(self, draft):
        obligee = draft.obligee
        return admin_obj_link(obligee, u'\n%s' % obligee.name, show_pk=True) if obligee else u'--'

    def get_fieldsets(self, request, obj=None):
        if obj is None:
            return self.fieldsets_add
        return super(InforequestDraftAdmin, self).get_fieldsets(request, obj)

    def get_form(self, request, obj=None, **kwargs):
        if obj is None:
            return InforequestDraftAdminAddForm
        return super(InforequestDraftAdmin, self).get_form(request, obj, **kwargs)

    def get_formsets(self, request, obj=None):
        if obj is None:
            return []
        return super(InforequestDraftAdmin, self).get_formsets(request, obj)


class InforequestAdminBranchInline(admin.TabularInline):
    model = Branch
    extra = 0

    fields = [
            u'branch_field',
            u'obligee_field',
            u'main_branch_field',
            ]
    readonly_fields = fields

    @decorate(short_description=_(u'Branch'))
    @decorate(allow_tags=True)
    def branch_field(self, branch):
        return admin_obj_link(branch)

    @decorate(short_description=_(u'Obligee'))
    @decorate(allow_tags=True)
    def obligee_field(self, branch):
        obligee = branch.obligee
        return admin_obj_link(obligee, obligee.name)

    @decorate(short_description=_(u'Main Branch'))
    @decorate(boolean=True)
    def main_branch_field(self, branch):
        return branch.is_main

    def has_add_permission(self, request):
        return False

    def has_delete_permission(self, request, obj=None):
        return False

class InforequestAdminInforequestEmailInline(admin.TabularInline):
    model = InforequestEmail
    extra = 0

    fields = [
            u'inforequestemail_field',
            u'email_field',
            u'email_type_field',
            u'email_from_field',
            u'type',
            ]
    readonly_fields = fields

    @decorate(short_description=_(u'Inforequest E-mail'))
    @decorate(allow_tags=True)
    def inforequestemail_field(self, inforequestemail):
        return admin_obj_link(inforequestemail)

    @decorate(short_description=_(u'E-mail'))
    @decorate(allow_tags=True)
    def email_field(self, inforequestemail):
        email = inforequestemail.email
        return admin_obj_link(email)

    @decorate(short_description=_(u'E-mail Type'))
    def email_type_field(self, inforequestemail):
        return inforequestemail.email.get_type_display()

    @decorate(short_description=_(u'From'))
    def email_from_field(self, inforequestemail):
        return inforequestemail.email.from_formatted

    def has_add_permission(self, request):
        return False

    def has_delete_permission(self, request, obj=None):
        return False

class InforequestAdminActionDraftInline(admin.TabularInline):
    model = ActionDraft
    extra = 0

    fields = [
            u'actiondraft_field',
            u'branch_field',
            u'branch_obligee_field',
            u'type',
            ]
    readonly_fields = fields

    @decorate(short_description=_(u'Action Draft'))
    @decorate(allow_tags=True)
    def actiondraft_field(self, draft):
        return admin_obj_link(draft)

    @decorate(short_description=_(u'Branch'))
    @decorate(allow_tags=True)
    def branch_field(self, draft):
        branch = draft.branch
        return admin_obj_link(branch) if branch else u'--'

    @decorate(short_description=_(u'Obligee'))
    @decorate(allow_tags=True)
    def branch_obligee_field(self, draft):
        obligee = draft.branch.obligee if draft.branch else None
        return admin_obj_link(obligee, obligee.name) if obligee else u'--'

    def has_add_permission(self, request):
        return False

    def has_delete_permission(self, request, obj=None):
        return False

class InforequestAdminAddForm(forms.Form):
    applicant = Inforequest._meta.get_field(u'applicant').formfield(
            widget=admin.widgets.ForeignKeyRawIdWidget(
                Inforequest._meta.get_field(u'applicant').rel, admin.site),
            )
    obligee = Branch._meta.get_field(u'obligee').formfield(
            widget=admin.widgets.ForeignKeyRawIdWidget(
                Branch._meta.get_field(u'obligee').rel, admin.site),
            )
    subject = Action._meta.get_field(u'subject').formfield(
            widget=admin.widgets.AdminTextInputWidget(),
            )
    content = Action._meta.get_field(u'content').formfield(
            widget=admin.widgets.AdminTextareaWidget(),
            )
    send_email = forms.BooleanField(
            required=False,
            help_text=squeeze(_(u"""
                Check to send the inforequest to the obligee by e-mail. Leave the checkbox empty if
                you just want to create a fake inforequest without sending any real e-mail to the
                obligee.
                """)),
            )
    # FIXME: attachments

    def save(self, commit=True):
        # Django admin runs it with commit=False only
        assert commit is False
        assert self.is_valid()

        inforequest = Inforequest(
                applicant=self.cleaned_data[u'applicant'],
                )

        @after_saved(inforequest)
        def deferred():
            branch = Branch(
                    inforequest=inforequest,
                    obligee=self.cleaned_data[u'obligee'],
                    )
            branch.save()

            action = Action(
                    branch=branch,
                    type=Action.TYPES.REQUEST,
                    subject=self.cleaned_data[u'subject'],
                    content=self.cleaned_data[u'content'],
                    effective_date=inforequest.submission_date,
                    )
            action.save()

            if self.cleaned_data[u'send_email']:
                action.send_by_email()

        return inforequest

    def save_m2m(self):
        pass

class InforequestAdmin(admin.ModelAdmin):
    list_display = [
            u'inforequest_column',
            u'applicant_column',
            u'obligee_column',
            u'unique_email',
            u'submission_date',
            u'closed',
            u'undecided_emails_column',
            ]
    list_filter = [
            u'submission_date',
            simple_list_filter_factory(_(u'Undecided E-mail'), u'undecided', [
                (u'1', _(u'With'), lambda qs: qs.filter(undecided__count__gt=0)),
                (u'0', _(u'Without'), lambda qs: qs.filter(undecided__count=0)),
                ]),
            u'closed',
            ]
    search_fields = [
            u'=id',
            u'applicant__first_name',
            u'applicant__last_name',
            u'applicant__email',
            u'branch__obligee__name',
            u'unique_email',
            ]

    @decorate(short_description=_(u'Inforequest'))
    @decorate(admin_order_field=u'pk')
    def inforequest_column(self, inforequest):
        return u'<%s: %s>' % (inforequest.__class__.__name__, inforequest.pk)

    @decorate(short_description=_(u'Applicant'))
    @decorate(admin_order_field=u'applicant__email')
    @decorate(allow_tags=True)
    def applicant_column(self, inforequest):
        user = inforequest.applicant
        return admin_obj_link(user, u'%s <%s>' % (user.get_full_name(), user.email))

    @decorate(short_description=_(u'Obligee'))
    @decorate(admin_order_field=u'branch__obligee__name')
    @decorate(allow_tags=True)
    def obligee_column(self, inforequest):
        obligee = inforequest.branch.obligee
        return admin_obj_link(obligee, obligee.name)

    @decorate(short_description=_(u'Undecided E-mails'))
    @decorate(admin_order_field=u'undecided__count')
    def undecided_emails_column(self, inforequest):
        return inforequest.undecided__count

    fieldsets = [
            (None, {
                u'classes': [u'wide'],
                u'fields': [
                    u'applicant',
                    u'applicant_details_field',
                    u'obligee_details_field',
                    u'applicant_name',
                    (u'applicant_street', u'applicant_city', u'applicant_zip'),
                    u'unique_email',
                    u'submission_date',
                    u'closed',
                    u'undecided_emails_field',
                    ],
                }),
            (_(u'Advanced'), {
                u'classes': [u'wide', u'collapse'],
                u'fields': [
                    u'last_undecided_email_reminder',
                    ],
                }),
            ]
    fieldsets_add = [
            (None, {
                u'fields': [
                    u'applicant',
                    u'obligee',
                    u'subject',
                    u'content',
                    u'send_email',
                    ],
                }),
            ]
    readonly_fields = [
            u'applicant_details_field',
            u'obligee_details_field',
            u'submission_date',
            u'undecided_emails_field',
            ]
    raw_id_fields = [
            u'applicant',
            ]
    inlines = [
            InforequestAdminBranchInline,
            InforequestAdminInforequestEmailInline,
            InforequestAdminActionDraftInline,
            ]

    @decorate(short_description=u'%s%s' % (ADMIN_FIELD_INDENT, _(u'Details')))
    @decorate(allow_tags=True)
    def applicant_details_field(self, inforequest):
        user = inforequest.applicant
        return admin_obj_link(user, u'\n%s <%s>' % (user.get_full_name(), user.email), show_pk=True)

    @decorate(short_description=_(u'Obligee'))
    @decorate(allow_tags=True)
    def obligee_details_field(self, inforequest):
        obligee = inforequest.branch.obligee
        return admin_obj_link(obligee, u'\n%s' % obligee.name, show_pk=True) if obligee else u'--'

    @decorate(short_description=_(u'Undecided E-mails'))
    def undecided_emails_field(self, inforequest):
        return inforequest.undecided_set.count()

    def get_queryset(self, request):
        queryset = super(InforequestAdmin, self).get_queryset(request)
        # We are interested in main branches only
        queryset = queryset.filter(branch__advanced_by__isnull=True)
        # Count undecided emails
        queryset = queryset.annotate(undecided__count=Count(u'inforequestemail',
            only=Q(inforequestemail__type=InforequestEmail.TYPES.UNDECIDED)))
        return queryset

    def get_fieldsets(self, request, obj=None):
        if obj is None:
            return self.fieldsets_add
        return super(InforequestAdmin, self).get_fieldsets(request, obj)

    def get_form(self, request, obj=None, **kwargs):
        if obj is None:
            return InforequestAdminAddForm
        return super(InforequestAdmin, self).get_form(request, obj, **kwargs)

    def get_formsets(self, request, obj=None):
        if obj is None:
            return []
        return super(InforequestAdmin, self).get_formsets(request, obj)


class InforequestEmailAdmin(admin.ModelAdmin):
    list_display = [
            u'inforequestemail_column',
            u'inforequest_column',
            u'inforequest_closed_column',
            u'inforequest_applicant_column',
            u'email_column',
            u'email_from_column',
            u'type',
            ]
    list_filter = [
            u'type',
            u'inforequest__closed',
            ]
    search_fields = [
            u'=id',
            u'=inforequest__pk',
            u'inforequest__applicant__first_name',
            u'inforequest__applicant__last_name',
            u'inforequest__applicant__email',
            u'=email__pk',
            u'email__from_mail',
            ]

    @decorate(short_description=_(u'Inforequest E-mail'))
    @decorate(admin_order_field=u'pk')
    def inforequestemail_column(self, inforequestemail):
        return u'<%s: %s>' % (inforequestemail.__class__.__name__, inforequestemail.pk)

    @decorate(short_description=_(u'Inforequest'))
    @decorate(admin_order_field=u'inforequest__pk')
    @decorate(allow_tags=True)
    def inforequest_column(self, inforequestemail):
        inforequest = inforequestemail.inforequest
        return admin_obj_link(inforequest)

    @decorate(short_description=_(u'Closed'))
    @decorate(admin_order_field=u'inforequest__closed')
    @decorate(boolean=True)
    def inforequest_closed_column(self, inforequestemail):
        return inforequestemail.inforequest.closed

    @decorate(short_description=_(u'Applicant'))
    @decorate(admin_order_field=u'inforequest__applicant__email')
    @decorate(allow_tags=True)
    def inforequest_applicant_column(self, inforequestemail):
        user = inforequestemail.inforequest.applicant
        return admin_obj_link(user, u'%s <%s>' % (user.get_full_name(), user.email))

    @decorate(short_description=_(u'E-mail'))
    @decorate(admin_order_field=u'email__pk')
    @decorate(allow_tags=True)
    def email_column(self, inforequestemail):
        email = inforequestemail.email
        return admin_obj_link(email)

    @decorate(short_description=_(u'From'))
    @decorate(admin_order_field=u'email__from_mail')
    def email_from_column(self, inforequestemail):
        return inforequestemail.email.from_mail

    fieldsets = [
            (None, {
                u'classes': [u'wide'],
                u'fields': [
                    u'inforequest',
                    u'inforequest_details_field',
                    u'inforequest_applicant_field',
                    u'inforequest_closed_field',
                    u'email',
                    u'email_details_field',
                    u'email_from_field',
                    u'email_subject_field',
                    u'type',
                    ],
                }),
            ]
    raw_id_fields = [
            u'inforequest',
            u'email',
            ]
    readonly_fields = [
            u'inforequest_details_field',
            u'inforequest_applicant_field',
            u'inforequest_closed_field',
            u'email_details_field',
            u'email_from_field',
            u'email_subject_field',
            ]
    inlines = [
            ]

    @decorate(short_description=u'%s%s' % (ADMIN_FIELD_INDENT, _(u'Details')))
    @decorate(allow_tags=True)
    def inforequest_details_field(self, inforequestemail):
        inforequest = inforequestemail.inforequest
        return admin_obj_link(inforequest)

    @decorate(short_description=u'%s%s' % (ADMIN_FIELD_INDENT, _(u'Applicant')))
    @decorate(allow_tags=True)
    def inforequest_applicant_field(self, inforequestemail):
        user = inforequestemail.inforequest.applicant
        return admin_obj_link(user, u'\n%s <%s>' % (user.get_full_name(), user.email), show_pk=True)

    @decorate(short_description=u'%s%s' % (ADMIN_FIELD_INDENT, _(u'Closed')))
    @decorate(boolean=True)
    def inforequest_closed_field(self, inforequestemail):
        return inforequestemail.inforequest.closed

    @decorate(short_description=u'%s%s' % (ADMIN_FIELD_INDENT, _(u'Details')))
    @decorate(allow_tags=True)
    def email_details_field(self, inforequestemail):
        email = inforequestemail.email
        return admin_obj_link(email)

    @decorate(short_description=u'%s%s' % (ADMIN_FIELD_INDENT, _(u'From')))
    def email_from_field(self, inforequestemail):
        return inforequestemail.email.from_formatted

    @decorate(short_description=u'%s%s' % (ADMIN_FIELD_INDENT, _(u'Subject')))
    def email_subject_field(self, inforequestemail):
        return inforequestemail.email.subject

    def has_add_permission(self, request):
        return False

    def has_delete_permission(self, request, obj=None):
        return False

    def get_queryset(self, request):
        queryset = super(InforequestEmailAdmin, self).get_queryset(request)
        # We are interested in main branches only now
        queryset = queryset.filter(inforequest__branch__advanced_by__isnull=True)
        return queryset


class BranchAdminActionInline(admin.TabularInline):
    model = Action
    extra = 0

    fields = [
            u'action_field',
            u'email_field',
            u'type',
            u'effective_date',
            u'deadline_details_field',
            ]
    readonly_fields = fields

    @decorate(short_description=_(u'Action'))
    @decorate(allow_tags=True)
    def action_field(self, action):
        return admin_obj_link(action)

    @decorate(short_description=_(u'E-mail'))
    @decorate(allow_tags=True)
    def email_field(self, action):
        email = action.email
        return admin_obj_link(email) if email else u'--'

    @decorate(short_description=_(u'Deadline'))
    def deadline_details_field(self, action):
        return action_deadline_details(action)

    def has_add_permission(self, request):
        return False

    def has_delete_permission(self, request, obj=None):
        return False

class BranchAdminAddForm(forms.Form):
    obligee = Branch._meta.get_field(u'obligee').formfield(
            widget=admin.widgets.ForeignKeyRawIdWidget(
                Branch._meta.get_field(u'obligee').rel, admin.site),
            )
    advanced_by = Branch._meta.get_field(u'advanced_by').formfield(
            required=True,
            widget=admin.widgets.ForeignKeyRawIdWidget(
                Branch._meta.get_field(u'advanced_by').rel, admin.site),
            )

    def save(self, commit=True):
        # Django admin runs it with commit=False only
        assert commit is False
        assert self.is_valid()

        branch = Branch(
                inforequest=self.cleaned_data[u'advanced_by'].branch.inforequest,
                obligee=self.cleaned_data[u'obligee'],
                advanced_by=self.cleaned_data[u'advanced_by'],
                )

        @after_saved(branch)
        def deferred():
            action = Action(
                    branch=branch,
                    effective_date=self.cleaned_data[u'advanced_by'].effective_date,
                    type=Action.TYPES.ADVANCED_REQUEST,
                    )
            action.save()

        return branch

    def save_m2m(self):
        pass

class BranchAdmin(admin.ModelAdmin):
    list_display = [
            u'branch_column',
            u'inforequest_column',
            u'inforequest_closed_column',
            u'inforequest_applicant_column',
            u'obligee_column',
            u'main_branch_column',
            ]
    list_filter = [
            simple_list_filter_factory(_(u'Main Branch'), u'mainbranch', [
                (u'1', _(u'Yes'), lambda qs: qs.main()),
                (u'0', _(u'No'),  lambda qs: qs.advanced()),
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

    @decorate(short_description=_(u'Branch'))
    @decorate(admin_order_field=u'pk')
    def branch_column(self, branch):
        return u'<%s: %s>' % (branch.__class__.__name__, branch.pk)

    @decorate(short_description=_(u'Inforequest'))
    @decorate(admin_order_field=u'inforequest__pk')
    @decorate(allow_tags=True)
    def inforequest_column(self, branch):
        inforequest = branch.inforequest
        return admin_obj_link(inforequest)

    @decorate(short_description=_(u'Closed'))
    @decorate(admin_order_field=u'inforequest__closed')
    @decorate(boolean=True)
    def inforequest_closed_column(self, inforequestemail):
        return inforequestemail.inforequest.closed

    @decorate(short_description=_(u'Applicant'))
    @decorate(admin_order_field=u'inforequest__applicant__email')
    @decorate(allow_tags=True)
    def inforequest_applicant_column(self, branch):
        user = branch.inforequest.applicant
        return admin_obj_link(user, u'%s <%s>' % (user.get_full_name(), user.email))

    @decorate(short_description=_(u'Obligee'))
    @decorate(admin_order_field=u'obligee__name')
    @decorate(allow_tags=True)
    def obligee_column(self, branch):
        obligee = branch.obligee
        return admin_obj_link(obligee, obligee.name)

    @decorate(short_description=_(u'Main Branch'))
    @decorate(admin_order_field=u'advanced_by')
    @decorate(boolean=True)
    def main_branch_column(self, branch):
        return branch.is_main

    fieldsets = [
            (None, {
                u'fields': [
                    u'inforequest',
                    u'inforequest_details_field',
                    u'inforequest_applicant_field',
                    u'inforequest_closed_field',
                    u'obligee',
                    u'obligee_details_field',
                    u'historicalobligee',
                    u'historicalobligee_details_field',
                    u'advanced_by',
                    u'advanced_by_details_field',
                    ],
                }),
            ]
    fieldsets_add = [
            (None, {
                u'fields': [
                    u'obligee',
                    u'advanced_by',
                    ],
                }),
            ]
    raw_id_fields = [
            u'inforequest',
            u'obligee',
            u'historicalobligee',
            u'advanced_by',
            ]
    readonly_fields = [
            u'inforequest_details_field',
            u'inforequest_applicant_field',
            u'inforequest_closed_field',
            u'obligee_details_field',
            u'historicalobligee_details_field',
            u'advanced_by_details_field',
            ]
    inlines = [
            BranchAdminActionInline,
            ]

    @decorate(short_description=u'%s%s' % (ADMIN_FIELD_INDENT, _(u'Details')))
    @decorate(allow_tags=True)
    def inforequest_details_field(self, branch):
        inforequest = branch.inforequest
        return admin_obj_link(inforequest)

    @decorate(short_description=u'%s%s' % (ADMIN_FIELD_INDENT, _(u'Applicant')))
    @decorate(allow_tags=True)
    def inforequest_applicant_field(self, branch):
        user = branch.inforequest.applicant
        return admin_obj_link(user, u'\n%s <%s>' % (user.get_full_name(), user.email), show_pk=True)

    @decorate(short_description=u'%s%s' % (ADMIN_FIELD_INDENT, _(u'Closed')))
    @decorate(boolean=True)
    def inforequest_closed_field(self, branch):
        return branch.inforequest.closed

    @decorate(short_description=u'%s%s' % (ADMIN_FIELD_INDENT, _(u'Details')))
    @decorate(allow_tags=True)
    def obligee_details_field(self, branch):
        obligee = branch.obligee
        return admin_obj_link(obligee, u'\n%s' % obligee.name, show_pk=True)

    @decorate(short_description=u'%s%s' % (ADMIN_FIELD_INDENT, _(u'Details')))
    @decorate(allow_tags=True)
    def historicalobligee_details_field(self, branch):
        historical = branch.historicalobligee
        return admin_obj_link(historical, u'\n%s' % historical.name, show_pk=True)

    @decorate(short_description=u'%s%s' % (ADMIN_FIELD_INDENT, _(u'Details')))
    @decorate(allow_tags=True)
    def advanced_by_details_field(self, branch):
        action = branch.advanced_by
        return admin_obj_link(action, u' %s' % action.get_type_display(), show_pk=True) if action else u'--'

    def has_delete_permission(self, request, obj=None):
        return False

    def get_fieldsets(self, request, obj=None):
        if obj is None:
            return self.fieldsets_add
        return super(BranchAdmin, self).get_fieldsets(request, obj)

    def get_form(self, request, obj=None, **kwargs):
        if obj is None:
            return BranchAdminAddForm
        return super(BranchAdmin, self).get_form(request, obj, **kwargs)

    def get_formsets(self, request, obj=None):
        if obj is None:
            return []
        return super(BranchAdmin, self).get_formsets(request, obj)


class ActionAdminAdvancedToInline(admin.TabularInline):
    model = Branch
    extra = 0
    verbose_name = _(u'Advanced To Branch')
    verbose_name_plural = _(u'Advanced To Branches')

    fields = [
            u'branch_field',
            u'obligee_field',
            ]
    readonly_fields = fields

    @decorate(short_description=_(u'Branch'))
    @decorate(allow_tags=True)
    def branch_field(self, branch):
        return admin_obj_link(branch)

    @decorate(short_description=_(u'Obligee'))
    @decorate(allow_tags=True)
    def obligee_field(self, branch):
        obligee = branch.obligee
        return admin_obj_link(obligee, obligee.name)

    def has_add_permission(self, request):
        return False

    def has_delete_permission(self, request, obj=None):
        return False

class ActionAdminAddForm(forms.Form):
    branch = Action._meta.get_field(u'branch').formfield(
            widget=admin.widgets.ForeignKeyRawIdWidget(
                Action._meta.get_field(u'branch').rel, admin.site),
            )
    type = Action._meta.get_field(u'type').formfield(
            )
    subject = Action._meta.get_field(u'subject').formfield(
            widget=admin.widgets.AdminTextInputWidget(),
            )
    content = Action._meta.get_field(u'content').formfield(
            widget=admin.widgets.AdminTextareaWidget(),
            )
    effective_date = Action._meta.get_field(u'effective_date').formfield(
            widget=admin.widgets.AdminDateWidget(),
            )
    deadline = Action._meta.get_field(u'deadline').formfield(
            widget=admin.widgets.AdminIntegerFieldWidget(),
            )
    extension = Action._meta.get_field(u'extension').formfield(
            widget=admin.widgets.AdminIntegerFieldWidget(),
            )
    disclosure_level = Action._meta.get_field(u'disclosure_level').formfield(
            )
    refusal_reason = Action._meta.get_field(u'refusal_reason').formfield(
            )
    obligee_set = ActionDraft._meta.get_field(u'obligee_set').formfield(
            widget=admin.widgets.ManyToManyRawIdWidget(
                ActionDraft._meta.get_field(u'obligee_set').rel, admin.site),
            )
    send_email = forms.BooleanField(
            required=False,
            help_text=squeeze(_(u"""
                Check to send an e-mail with the created action to the obligee. Leave the checkbox
                empty if do not want to send any e-mail. Applicable for applicant actions only.
                """)),
            )
    # FIXME: attachments

    def clean(self):
        cleaned_data = super(ActionAdminAddForm, self).clean()

        if u'send_email' in cleaned_data and u'type' in cleaned_data:
            if cleaned_data[u'send_email'] and cleaned_data[u'type'] not in Action.APPLICANT_ACTION_TYPES:
                self._errors[u'send_email'] = self.error_class([_(u'Ony applicant actions may be send by e-mail.')])
                del cleaned_data[u'send_email']

        return cleaned_data

    def save(self, commit=True):
        # Django admin runs it with commit=False only
        assert commit is False
        assert self.is_valid()

        action = Action(
                branch=self.cleaned_data[u'branch'],
                type=self.cleaned_data[u'type'],
                subject=self.cleaned_data[u'subject'],
                content=self.cleaned_data[u'content'],
                effective_date=self.cleaned_data[u'effective_date'],
                deadline=self.cleaned_data[u'deadline'],
                extension=self.cleaned_data[u'extension'],
                disclosure_level=self.cleaned_data[u'disclosure_level'],
                refusal_reason=self.cleaned_data[u'refusal_reason'],
                )

        @after_saved(action)
        def deferred():
            for obligee in self.cleaned_data[u'obligee_set']:
                sub_branch = Branch(
                        inforequest=action.branch.inforequest,
                        obligee=obligee,
                        advanced_by=action,
                        )
                sub_branch.save()

                sub_action = Action(
                        branch=sub_branch,
                        type=Action.TYPES.ADVANCED_REQUEST,
                        effective_date=action.effective_date,
                        )
                sub_action.save()

            if self.cleaned_data[u'send_email']:
                action.send_by_email()

        return action

    def save_m2m(self):
        pass

class ActionAdmin(admin.ModelAdmin):
    list_display = [
            u'action_column',
            u'branch_column',
            u'branch_inforequest_column',
            u'branch_closed_column',
            u'branch_applicant_column',
            u'branch_obligee_column',
            u'email_column',
            u'type',
            u'effective_date',
            ]
    list_filter = [
            u'type',
            u'effective_date',
            simple_list_filter_factory(_(u'E-mail'), u'email', [
                (u'1', _(u'Yes'), lambda qs: qs.by_email()),
                (u'0', _(u'No'),  lambda qs: qs.by_smail()),
                ]),
            u'branch__inforequest__closed',
            ]
    search_fields = [
            u'=id',
            u'=branch__pk',
            u'=branch__inforequest__pk',
            u'branch__inforequest__applicant__first_name',
            u'branch__inforequest__applicant__last_name',
            u'branch__inforequest__applicant__email',
            u'branch__obligee__name',
            u'=email__pk',
            ]

    @decorate(short_description=_(u'Action'))
    @decorate(admin_order_field=u'pk')
    def action_column(self, action):
        return u'<%s: %s>' % (action.__class__.__name__, action.pk)

    @decorate(short_description=_(u'Branch'))
    @decorate(admin_order_field=u'branch__pk')
    @decorate(allow_tags=True)
    def branch_column(self, action):
        branch = action.branch
        return admin_obj_link(branch)

    @decorate(short_description=_(u'Inforequest'))
    @decorate(admin_order_field=u'branch__inforequest__pk')
    @decorate(allow_tags=True)
    def branch_inforequest_column(self, action):
        inforequest = action.branch.inforequest
        return admin_obj_link(inforequest)

    @decorate(short_description=_(u'Closed'))
    @decorate(admin_order_field=u'branch__inforequest__closed')
    @decorate(boolean=True)
    def branch_closed_column(self, action):
        return action.branch.inforequest.closed

    @decorate(short_description=_(u'Applicant'))
    @decorate(admin_order_field=u'branch__inforequest__applicant__email')
    @decorate(allow_tags=True)
    def branch_applicant_column(self, action):
        user = action.branch.inforequest.applicant
        return admin_obj_link(user, u'%s <%s>' % (user.get_full_name(), user.email))

    @decorate(short_description=_(u'Obligee'))
    @decorate(admin_order_field=u'branch__obligee__name')
    @decorate(allow_tags=True)
    def branch_obligee_column(self, action):
        obligee = action.branch.obligee
        return admin_obj_link(obligee, obligee.name)

    @decorate(short_description=_(u'Email'))
    @decorate(admin_order_field=u'email__pk')
    @decorate(allow_tags=True)
    def email_column(self, action):
        email = action.email
        return admin_obj_link(email) if email else u'--'

    fieldsets = [
            (None, {
                u'classes': [u'wide'],
                u'fields': [
                    u'branch',
                    u'branch_details_field',
                    u'branch_inforequest_field',
                    u'branch_applicant_field',
                    u'branch_obligee_field',
                    u'branch_closed_field',
                    u'email',
                    u'email_details_field',
                    u'email_from_field',
                    u'email_subject_field',
                    u'type',
                    u'type_details_field',
                    u'subject',
                    u'content',
                    u'effective_date',
                    u'deadline',
                    u'extension',
                    u'deadline_details_field',
                    u'disclosure_level',
                    u'refusal_reason',
                    ],
                }),
            (_(u'Advanced'), {
                u'classes': [u'wide', u'collapse'],
                u'fields': [
                    u'last_deadline_reminder',
                    ],
                }),
            ]
    fieldsets_add = [
            (None, {
                u'classes': [u'wide'],
                u'fields': [
                    u'branch',
                    u'type',
                    u'subject',
                    u'content',
                    u'effective_date',
                    u'deadline',
                    u'extension',
                    u'disclosure_level',
                    u'refusal_reason',
                    u'obligee_set',
                    u'send_email',
                    ],
                }),
            ]
    raw_id_fields = [
            u'branch',
            u'email',
            ]
    readonly_fields = [
            u'branch_details_field',
            u'branch_inforequest_field',
            u'branch_applicant_field',
            u'branch_obligee_field',
            u'branch_closed_field',
            u'email_details_field',
            u'email_from_field',
            u'email_subject_field',
            u'type_details_field',
            u'deadline_details_field',
            ]
    inlines = [
            AttachmentInline,
            ActionAdminAdvancedToInline,
            ]

    @decorate(short_description=u'%s%s' % (ADMIN_FIELD_INDENT, _(u'Details')))
    @decorate(allow_tags=True)
    def branch_details_field(self, action):
        branch = action.branch
        return admin_obj_link(branch)

    @decorate(short_description=u'%s%s' % (ADMIN_FIELD_INDENT, _(u'Inforequest')))
    @decorate(allow_tags=True)
    def branch_inforequest_field(self, action):
        inforequest = action.branch.inforequest
        return admin_obj_link(inforequest)

    @decorate(short_description=u'%s%s' % (ADMIN_FIELD_INDENT, _(u'Applicant')))
    @decorate(allow_tags=True)
    def branch_applicant_field(self, action):
        user = action.branch.inforequest.applicant
        return admin_obj_link(user, u'\n%s <%s>' % (user.get_full_name(), user.email), show_pk=True)

    @decorate(short_description=u'%s%s' % (ADMIN_FIELD_INDENT, _(u'Obligee')))
    @decorate(allow_tags=True)
    def branch_obligee_field(self, action):
        obligee = action.branch.obligee
        return admin_obj_link(obligee, u'\n%s' % obligee.name, show_pk=True)

    @decorate(short_description=u'%s%s' % (ADMIN_FIELD_INDENT, _(u'Closed')))
    @decorate(boolean=True)
    def branch_closed_field(self, action):
        return action.branch.inforequest.closed

    @decorate(short_description=u'%s%s' % (ADMIN_FIELD_INDENT, _(u'Details')))
    @decorate(allow_tags=True)
    def email_details_field(self, action):
        email = action.email
        return admin_obj_link(email)

    @decorate(short_description=u'%s%s' % (ADMIN_FIELD_INDENT, _(u'From')))
    def email_from_field(self, action):
        return action.email.from_formatted

    @decorate(short_description=u'%s%s' % (ADMIN_FIELD_INDENT, _(u'Subject')))
    def email_subject_field(self, action):
        return action.email.subject

    @decorate(short_description=u'%s%s' % (ADMIN_FIELD_INDENT, _(u'Details')))
    def type_details_field(self, action):
        if action.is_applicant_action:
            return _(u'Applicant Action')
        if action.is_obligee_action:
            return _(u'Obligee Action')
        if action.is_implicit_action:
            return _(u'Implicit Action')

    @decorate(short_description=u'%s%s' % (ADMIN_FIELD_INDENT, _(u'Details')))
    def deadline_details_field(self, action):
        return action_deadline_details(action)

    def get_fieldsets(self, request, obj=None):
        if obj is None:
            return self.fieldsets_add
        return super(ActionAdmin, self).get_fieldsets(request, obj)

    def get_form(self, request, obj=None, **kwargs):
        if obj is None:
            return ActionAdminAddForm
        return super(ActionAdmin, self).get_form(request, obj, **kwargs)

    def get_formsets(self, request, obj=None):
        if obj is None:
            return []
        return super(ActionAdmin, self).get_formsets(request, obj)


class ActionDraftAdmin(admin.ModelAdmin):
    list_display = [
            u'actiondraft_column',
            u'inforequest_column',
            u'inforequest_closed_column',
            u'inforequest_applicant_column',
            u'branch_column',
            u'branch_obligee_column',
            u'type',
            ]
    list_filter = [
            u'type',
            u'inforequest__closed',
            ]
    search_fields = [
            u'=id',
            u'=inforequest__pk',
            u'inforequest__applicant__first_name',
            u'inforequest__applicant__last_name',
            u'inforequest__applicant__email',
            u'=branch__pk',
            u'branch__obligee__name',
            ]

    @decorate(short_description=_(u'Action Draft'))
    @decorate(admin_order_field=u'pk')
    def actiondraft_column(self, draft):
        return u'<%s: %s>' % (draft.__class__.__name__, draft.pk)

    @decorate(short_description=_(u'Inforequest'))
    @decorate(admin_order_field=u'inforequest__pk')
    @decorate(allow_tags=True)
    def inforequest_column(self, draft):
        inforequest = draft.inforequest
        return admin_obj_link(inforequest)

    @decorate(short_description=_(u'Closed'))
    @decorate(admin_order_field=u'inforequest__closed')
    @decorate(boolean=True)
    def inforequest_closed_column(self, draft):
        return draft.inforequest.closed

    @decorate(short_description=_(u'Applicant'))
    @decorate(admin_order_field=u'inforequest__applicant__email')
    @decorate(allow_tags=True)
    def inforequest_applicant_column(self, draft):
        user = draft.inforequest.applicant
        return admin_obj_link(user, u'%s <%s>' % (user.get_full_name(), user.email))

    @decorate(short_description=_(u'Branch'))
    @decorate(admin_order_field=u'branch__pk')
    @decorate(allow_tags=True)
    def branch_column(self, draft):
        branch = draft.branch
        return admin_obj_link(branch) if branch else u'--'

    @decorate(short_description=_(u'Obligee'))
    @decorate(admin_order_field=u'branch__obligee__name')
    @decorate(allow_tags=True)
    def branch_obligee_column(self, draft):
        obligee = draft.branch.obligee if draft.branch else None
        return admin_obj_link(obligee, obligee.name) if obligee else u'--'

    fieldsets = [
            (None, {
                u'classes': [u'wide'],
                u'fields': [
                    u'inforequest',
                    u'inforequest_details_field',
                    u'inforequest_applicant_field',
                    u'inforequest_closed_field',
                    u'branch',
                    u'branch_details_field',
                    u'branch_obligee_field',
                    u'type',
                    u'subject',
                    u'content',
                    u'effective_date',
                    u'deadline',
                    u'disclosure_level',
                    u'refusal_reason',
                    u'obligee_set',
                    u'obligee_set_details_field',
                    ],
                }),
            ]
    raw_id_fields = [
            u'inforequest',
            u'branch',
            u'obligee_set',
            ]
    readonly_fields = [
            u'inforequest_details_field',
            u'inforequest_applicant_field',
            u'inforequest_closed_field',
            u'branch_details_field',
            u'branch_obligee_field',
            u'obligee_set_details_field',
            ]
    inlines = [
            AttachmentInline,
            ]

    @decorate(short_description=u'%s%s' % (ADMIN_FIELD_INDENT, _(u'Details')))
    @decorate(allow_tags=True)
    def inforequest_details_field(self, draft):
        inforequest = draft.inforequest
        return admin_obj_link(inforequest)

    @decorate(short_description=u'%s%s' % (ADMIN_FIELD_INDENT, _(u'Applicant')))
    @decorate(allow_tags=True)
    def inforequest_applicant_field(self, draft):
        user = draft.inforequest.applicant
        return admin_obj_link(user, u'\n%s <%s>' % (user.get_full_name(), user.email), show_pk=True)

    @decorate(short_description=u'%s%s' % (ADMIN_FIELD_INDENT, _(u'Closed')))
    @decorate(boolean=True)
    def inforequest_closed_field(self, draft):
        return draft.inforequest.closed

    @decorate(short_description=u'%s%s' % (ADMIN_FIELD_INDENT, _(u'Details')))
    @decorate(allow_tags=True)
    def branch_details_field(self, draft):
        branch = draft.branch
        return admin_obj_link(branch) if branch else u'--'

    @decorate(short_description=u'%s%s' % (ADMIN_FIELD_INDENT, _(u'Obligee')))
    @decorate(allow_tags=True)
    def branch_obligee_field(self, draft):
        obligee = draft.branch.obligee if draft.branch else None
        return admin_obj_link(obligee, u'\n%s' % obligee.name, show_pk=True) if obligee else u'--'

    @decorate(short_description=u'%s%s' % (ADMIN_FIELD_INDENT, _(u'Details')))
    @decorate(allow_tags=True)
    def obligee_set_details_field(self, draft):
        obligees = draft.obligee_set.all()
        return u'\n'.join(admin_obj_link(o, u' %s' % o.name, show_pk=True) for o in obligees) if obligees else u'--'

    def has_add_permission(self, request):
        return False


class UserAdminMixinInforequestInline(admin.TabularInline):
    model = Inforequest
    extra = 0

    fields = [
            u'inforequest_field',
            u'obligee_field',
            u'unique_email',
            u'submission_date',
            u'closed',
            u'has_undecided_field',
            ]
    readonly_fields = fields

    @decorate(short_description=_(u'Inforequest'))
    @decorate(allow_tags=True)
    def inforequest_field(self, inforequest):
        return admin_obj_link(inforequest)

    @decorate(short_description=_(u'Obligee'))
    @decorate(allow_tags=True)
    def obligee_field(self, inforequest):
        obligee = inforequest.branch.obligee
        return admin_obj_link(obligee, obligee.name)

    @decorate(short_description=_(u'Undecided E-mail'))
    @decorate(boolean=True)
    def has_undecided_field(self, inforequest):
        return inforequest.has_undecided_email

    def has_add_permission(self, request):
        return False

    def has_delete_permission(self, request, obj=None):
        return False

class UserAdminMixinInforequestDraftInline(admin.TabularInline):
    model = InforequestDraft
    extra = 0

    fields = [
            u'inforequestdraft_field',
            u'obligee_field',
            ]
    readonly_fields = fields

    @decorate(short_description=_(u'Inforequest Draft'))
    @decorate(allow_tags=True)
    def inforequestdraft_field(self, draft):
        return admin_obj_link(draft)

    @decorate(short_description=_(u'Obligee'))
    @decorate(allow_tags=True)
    def obligee_field(self, draft):
        obligee = draft.obligee
        return admin_obj_link(obligee, obligee.name) if obligee else u'--'

    def has_add_permission(self, request):
        return False

    def has_delete_permission(self, request, obj=None):
        return False

class UserAdminMixin(admin.ModelAdmin):
    def __init__(self, *args, **kwargs):
        self.list_display = list(self.list_display) + [
                u'inforequest_count_column',
                ]
        self.list_filter = list(self.list_filter) + [
            simple_list_filter_factory(_(u'Inforequests'), u'inforequests', [
                (u'1', _(u'With'), lambda qs: qs.filter(inforequest__count__gt=0)),
                (u'0', _(u'Without'), lambda qs: qs.filter(inforequest__count=0)),
                ]),
                ]
        self.inlines = list(self.inlines) + [
                UserAdminMixinInforequestInline,
                UserAdminMixinInforequestDraftInline,
                ]
        super(UserAdminMixin, self).__init__(*args, **kwargs)

    @decorate(short_description=_(u'Inforequests'))
    @decorate(admin_order_field=u'inforequest__count')
    def inforequest_count_column(self, user):
        return user.inforequest__count

    def get_queryset(self, request):
        queryset = super(UserAdminMixin, self).get_queryset(request)
        queryset = queryset.annotate(Count(u'inforequest'))
        return queryset

class MessageAdminMixin(admin.ModelAdmin):
    def __init__(self, *args, **kwargs):
        self.list_display = list(self.list_display) + [
                u'assigned_to_column',
                u'action_column',
                ]
        self.list_filter = list(self.list_filter) + [
                simple_list_filter_factory(_(u'Assigned'), u'assigned', [
                    (u'1', _(u'Yes'), lambda qs: qs.filter(inforequest__isnull=False).distinct()),
                    (u'0', _(u'No'),  lambda qs: qs.filter(inforequest__isnull=True)),
                    ]),
                simple_list_filter_factory(_(u'Action'), u'action', [
                    (u'1', _(u'Yes'), lambda qs: qs.filter(action__isnull=False).distinct()),
                    (u'0', _(u'No'),  lambda qs: qs.filter(action__isnull=True)),
                    ]),
                ]
        self.search_fields = list(self.search_fields) + [
                u'=inforequest__pk',
                u'=action__pk',
                ]
        self.fieldsets[0][1][u'fields'] = list(self.fieldsets[0][1][u'fields']) + [
                u'assigned_to_column',
                u'action_column',
                ]
        self.readonly_fields = list(self.readonly_fields) + [
                u'assigned_to_column',
                u'action_column',
                ]
        super(MessageAdminMixin, self).__init__(*args, **kwargs)

    @decorate(short_description=_(u'Assigned To'))
    @decorate(admin_order_field=u'inforequest__pk')
    @decorate(allow_tags=True)
    def assigned_to_column(self, message):
        return u', '.join(admin_obj_link(ir) for ir in message.inforequest_set.all()) or u'--'

    @decorate(short_description=_(u'Action'))
    @decorate(admin_order_field=u'action__pk')
    @decorate(allow_tags=True)
    def action_column(self, message):
        try:
            action = message.action
        except Action.DoesNotExist:
            action = None
        return admin_obj_link(action) if action else u'--'


admin.site.register(InforequestDraft, InforequestDraftAdmin)
admin.site.register(Inforequest, InforequestAdmin)
admin.site.register(InforequestEmail, InforequestEmailAdmin)
admin.site.register(Branch, BranchAdmin)
admin.site.register(Action, ActionAdmin)
admin.site.register(ActionDraft, ActionDraftAdmin)
extend_model_admin(User, UserAdminMixin)
extend_model_admin(Message, MessageAdminMixin)
