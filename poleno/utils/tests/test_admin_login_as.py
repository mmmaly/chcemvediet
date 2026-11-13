from django.contrib.auth.decorators import user_passes_test
from django.urls import include, re_path
from django.contrib.auth.models import User
from django.http import HttpResponse
from django.test import TestCase
from django.test.utils import override_settings


def public_view(request):
    if isinstance(request.user, User):
        pass  # force request.user to evaluate
    return HttpResponse()

@user_passes_test(lambda u: u.is_staff, login_url=u'/login/', redirect_field_name=u'next')
def admin_view(request):
    if isinstance(request.user, User):
        pass
    return HttpResponse()

@user_passes_test(lambda u: u.is_staff, login_url=u'/login/', redirect_field_name=u'next')
def set_admin_login_as_attribute_admin_view(request, obj_pk):
    request.session[u'admin_login_as'] = obj_pk
    if isinstance(request.user, User):
        pass
    return HttpResponse()

urlpatterns = [
        re_path(r'^$', public_view),
        re_path(r'^admin/', include(([
                re_path(r'^$', admin_view),
                re_path(r'^(\d+)/login-as/$', set_admin_login_as_attribute_admin_view),
        ], u'admin'))),
]


@override_settings(
        ROOT_URLCONF=__name__,
        AUTHENTICATION_BACKENDS=(u'django.contrib.auth.backends.ModelBackend',),
        PASSWORD_HASHERS=(u'django.contrib.auth.hashers.MD5PasswordHasher',),
        )
class AdminLoginAsMiddlewareTest(TestCase):
    u"""
    Tests ``AdminLoginAsMiddleware`` together with a view setting the ``admin_login_as`` session
    key like ``AdminLoginAsAdminMixin.login_as_view`` does.
    """

    def setUp(self):
        self.user = User.objects.create_user(
                username=u'user',
                email=u'user@example.com',
                password=u'test',
                )
        self.superuser = User.objects.create_superuser(
                username=u'superuser',
                email=u'superuser@example.com',
                password=u'test',
                )


    def test_public_route_uses_anonymous_user_if_user_is_not_logged_in(self):
        response = self.client.get(u'/')
        self.assertEqual(response.status_code, 200)
        self.assertTrue(response.wsgi_request.user.is_anonymous)

    def test_admin_route_uses_anonymous_user_and_fails_if_user_is_not_logged_in(self):
        response = self.client.get(u'/admin/')
        self.assertTrue(response.wsgi_request.user.is_anonymous)
        self.assertRedirects(response, u'/login/?next=/admin/', fetch_redirect_response=False)

    def test_public_route_uses_the_user_if_user_is_logged_in(self):
        self.assertTrue(self.client.login(username=self.user.username, password=u'test'))
        response = self.client.get(u'/')
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.wsgi_request.user, self.user)

    def test_admin_route_uses_the_user_and_fails_if_user_is_logged_in(self):
        self.assertTrue(self.client.login(username=self.user.username, password=u'test'))
        response = self.client.get(u'/admin/')
        self.assertRedirects(response, u'/login/?next=/admin/', fetch_redirect_response=False)
        self.assertEqual(response.wsgi_request.user, self.user)

    def test_public_route_uses_the_admin_if_admin_is_logged_in(self):
        self.assertTrue(self.client.login(username=self.superuser.username, password=u'test'))
        response = self.client.get(u'/')
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.wsgi_request.user, self.superuser)

    def test_admin_route_uses_the_admin_if_admin_is_logged_in(self):
        self.assertTrue(self.client.login(username=self.superuser.username, password=u'test'))
        response = self.client.get(u'/admin/')
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.wsgi_request.user, self.superuser)

    def test_public_route_uses_the_user_if_admin_is_logged_in_as_another_user(self):
        self.assertTrue(self.client.login(username=self.superuser.username, password=u'test'))
        self.client.get(u'/admin/{}/login-as/'.format(self.user.pk))
        response = self.client.get(u'/')
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.wsgi_request.user, self.user)

    def test_admin_route_uses_the_admin_if_admin_is_logged_in_as_another_user(self):
        self.assertTrue(self.client.login(username=self.superuser.username, password=u'test'))
        self.client.get(u'/admin/{}/login-as/'.format(self.user.pk))
        response = self.client.get(u'/admin/')
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.wsgi_request.user, self.superuser)

    def test_admin_stays_logged_in_after_visiting_public_route_as_another_user(self):
        self.assertTrue(self.client.login(username=self.superuser.username, password=u'test'))
        self.client.get(u'/admin/{}/login-as/'.format(self.user.pk))
        self.client.get(u'/')
        self.client.get(u'/')
        response = self.client.get(u'/admin/')
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.wsgi_request.user, self.superuser)

    def test_non_staff_user_can_not_log_in_as_another_user(self):
        self.assertTrue(self.client.login(username=self.user.username, password=u'test'))
        session = self.client.session
        session[u'admin_login_as'] = self.superuser.pk
        session.save()
        response = self.client.get(u'/')
        self.assertEqual(response.wsgi_request.user, self.user)

    def test_missing_user_falls_back_to_the_admin(self):
        self.assertTrue(self.client.login(username=self.superuser.username, password=u'test'))
        self.client.get(u'/admin/999999/login-as/')
        response = self.client.get(u'/')
        self.assertEqual(response.wsgi_request.user, self.superuser)
