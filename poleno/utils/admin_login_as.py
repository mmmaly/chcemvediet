from django.conf.urls import url
from django.contrib import admin
from django.contrib.auth.backends import ModelBackend
from django.urls import resolve, Resolver404
from django.http import HttpResponseRedirect

from poleno.utils.http import get_request
from poleno.utils.urls import reverse


class AdminLoginAsBackendMixin(ModelBackend):
    u"""
    Django authentication ModelBackend that allows admin to log in as any user (without being logged
    off) and perform any action on his behalf, without the admin knowing the user's password. Admin
    can simultaneously perform actions on admin page. Must be used together with
    ``AdminLoginAsAdminMixin``. Note that admin application namespace must be called 'admin'.

    Example:

        class MyApplicationBackend(AdminLoginAsBackendMixin, SomeAuthenticationBackend):
            ...

    Settings:

        AUTHENTICATION_BACKENDS = (
            'path.to.MyApplicationBackend',
            ...
        )
    """
    def is_admin_path(self, path):
        return resolve(path).namespace == u'admin'

    def get_user(self, user_id):
        request = get_request()
        user = super(AdminLoginAsBackendMixin, self).get_user(user_id)
        if request is None:
            return user
        try:
            resolve(request.path)
        except Resolver404:
            return user
        admin_login_as = request.session.get(u'admin_login_as')
        if user and user.is_staff and not self.is_admin_path(request.path) and admin_login_as:
            return super(AdminLoginAsBackendMixin, self).get_user(admin_login_as) or user
        return user

class AdminLoginAsAdminMixin(admin.ModelAdmin):
    u"""
    Django ModelAdmin that defines view, which allows admin to be simultaneously logged in as any
    user. Must be used together with ``AdminLoginAsBackendMixin``.

    Example:

        class MyModelAdmin(AdminLoginAsAdminMixin, admin.ModelAdmin):
            list_display = [
                    ...
                    decorate(
                        lambda o: admin_obj_format(o, u'Log in', link=u'login_as'),
                        ),
                    ]
            login_as_redirect_viewname = u'application:viewname'
            ...
    """
    def login_as_view(self, request, obj_pk):
        request.session[u'admin_login_as'] = obj_pk
        return HttpResponseRedirect(reverse(self.login_as_redirect_viewname))

    def get_urls(self):
        info = self.model._meta.app_label, self.model._meta.model_name
        login_as_view = self.admin_site.admin_view(self.login_as_view)
        urls = [
                url(r'^(\d+)/login-as/$', login_as_view, name=u'{}_{}_login_as'.format(*info)),
                ]
        return urls + super(AdminLoginAsAdminMixin, self).get_urls()
