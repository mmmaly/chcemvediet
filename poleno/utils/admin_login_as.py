from django.urls import re_path
from django.contrib import admin
from django.contrib.auth.models import User
from django.urls import resolve, Resolver404
from django.http import HttpResponseRedirect
from django.utils.deprecation import MiddlewareMixin
from django.utils.functional import SimpleLazyObject

from poleno.utils.urls import reverse


class AdminLoginAsMiddleware(MiddlewareMixin):
    u"""
    Middleware that allows admin to log in as any user (without being logged off) and perform any
    action on his behalf, without the admin knowing the user's password. Admin can simultaneously
    perform actions on admin page. Must be used together with ``AdminLoginAsAdminMixin``. Note that
    admin application namespace must be called 'admin'.

    The admin stays authenticated in the session as himself; only ``request.user`` is replaced
    outside the admin pages. Replacing the user already in the authentication backend does not
    work since Django 1.10: Django verifies the session hash against the returned user and logs
    the admin out when it does not match.

    Settings:

        MIDDLEWARE = (
            ...
            'django.contrib.auth.middleware.AuthenticationMiddleware',
            'django.middleware.locale.LocaleMiddleware',
            'poleno.utils.admin_login_as.AdminLoginAsMiddleware',
            ...
        )
    """
    def is_admin_path(self, path):
        return resolve(path).namespace == u'admin'

    def get_user(self, admin, admin_login_as):
        if not admin.is_staff:
            return admin
        return User.objects.filter(pk=admin_login_as).first() or admin

    def process_request(self, request):
        admin_login_as = request.session.get(u'admin_login_as')
        if not admin_login_as:
            return None
        try:
            if self.is_admin_path(request.path):
                return None
        except Resolver404:
            return None
        admin = request.user
        request.user = SimpleLazyObject(lambda: self.get_user(admin, admin_login_as))
        return None

class AdminLoginAsAdminMixin(admin.ModelAdmin):
    u"""
    Django ModelAdmin that defines view, which allows admin to be simultaneously logged in as any
    user. Must be used together with ``AdminLoginAsMiddleware``.

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
                re_path(r'^(\d+)/login-as/$', login_as_view, name=u'{}_{}_login_as'.format(*info)),
                ]
        return urls + super(AdminLoginAsAdminMixin, self).get_urls()
