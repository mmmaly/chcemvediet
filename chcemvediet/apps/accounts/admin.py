# vim: expandtab
# -*- coding: utf-8 -*-
from copy import deepcopy

from django.contrib import admin
from django.contrib.auth.models import User

from poleno.utils.misc import decorate
from poleno.utils.admin import admin_obj_format, extend_model_admin

from .models import Profile

ADMIN_FIELD_INDENT = u'    • '

class ProfileAdmin(admin.ModelAdmin):
    list_display = [
            u'profile_column',
            u'user_column',
            u'city',
            ]
    list_filter = [
            ]
    search_fields = [
            u'=id',
            u'user__first_name',
            u'user__last_name',
            u'user__email',
            u'city',
            ]
    ordering = [u'-pk']

    @decorate(short_description=u'Profile')
    @decorate(admin_order_field=u'pk')
    def profile_column(self, profile):
        return admin_obj_format(profile, link=False)

    @decorate(short_description=u'User')
    @decorate(admin_order_field=u'user__email')
    def user_column(self, profile):
        user = profile.user
        return admin_obj_format(user, u'{obj.first_name} {obj.last_name} <{obj.email}>')

    fields = [
            u'user_details_field',
            u'street',
            u'city',
            u'zip',
            ]
    readonly_fields = [
            u'user_details_field',
            ]
    raw_id_fields = [
            u'user',
            ]
    inlines = [
            ]

    @decorate(short_description=u'User')
    def user_details_field(self, profile):
        user = profile.user
        return admin_obj_format(user, u'{tag}\n{obj.first_name} {obj.last_name} <{obj.email}>')

    def has_add_permission(self, request):
        return False

    def has_delete_permission(self, request, obj=None):
        return False

    def get_queryset(self, request):
        queryset = super(ProfileAdmin, self).get_queryset(request)
        queryset = select_related(u'user')
        return queryset

class UserAdminMixin(admin.ModelAdmin):
    def __init__(self, *args, **kwargs):
        # We don't want to change predecessor internal objects
        self.fieldsets = deepcopy(self.fieldsets)

        self.fieldsets[0][1][u'fields'] = list(self.fieldsets[0][1][u'fields']) + [
                u'profile_field',
                ]
        self.readonly_fields = list(self.readonly_fields) + [
                u'profile_field',
                ]
        super(UserAdminMixin, self).__init__(*args, **kwargs)

    @decorate(short_description=u'Profile')
    def profile_field(self, user):
        profile = user.profile
        return admin_obj_format(profile)

admin.site.register(Profile, ProfileAdmin)
extend_model_admin(User, UserAdminMixin)
