from django.contrib.auth.decorators import user_passes_test
from django.conf.urls import url, RegexURLPattern
from django.contrib.auth.models import User
from django.http import HttpResponse
from django.test import TestCase
from django.test.utils import override_settings


class AdminLoginAsBackendMixinTest(TestCase):

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

    urls = [
            url(r'^$', public_view),
            url(r'admin/', ([
                    RegexURLPattern(r'^$', admin_view),
                    RegexURLPattern(r'^(\d+)/login-as/$', set_admin_login_as_attribute_admin_view),
            ], None, u'admin')),
    ]

    def create_users(self):
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

    def setUp(self):
        self.settings_override = override_settings(
            AUTHENTICATION_BACKENDS=(u'poleno.utils.admin_login_as.AdminLoginAsBackendMixin',),
            PASSWORD_HASHERS=(u'django.contrib.auth.hashers.MD5PasswordHasher',),
        )
        self.settings_override.enable()
        self.create_users()

    def tearDown(self):
        self.settings_override.disable()


    def test_public_route_uses_anonymous_user_if_user_is_not_logged_in(self):
        response = self.client.get(u'/')
        self.assertEqual(response.status_code, 200)
        self.assertTrue(response.wsgi_request.user.is_anonymous())

    def test_admin_route_uses_anonymous_user_and_fails_if_user_is_not_logged_in(self):
        response = self.client.get(u'/admin/')
        self.assertTrue(response.wsgi_request.user.is_anonymous())
        self.assertEqual(response.status_code, 302)
        self.assertRedirects(response, u'/login/?next=/admin/', fetch_redirect_response=False)

    def test_public_route_uses_the_user_if_user_is_logged_in(self):
        self.assertTrue(self.client.login(username=self.user.username, password=u'test'))
        response = self.client.get(u'/')
        self.assertEqual(response.status_code, 200)
        self.assertTrue(response.wsgi_request.user, self.user)

    def test_admin_route_uses_the_user_and_fails_if_user_is_logged_in(self):
        self.assertTrue(self.client.login(username=self.user.username, password=u'test'))
        response = self.client.get(u'/admin/')
        self.assertEqual(response.status_code, 302)
        self.assertRedirects(response, u'/login/?next=/admin/', fetch_redirect_response=False)
        self.assertEqual(response.wsgi_request.user, self.user)

    def test_public_route_uses_the_admin_if_admin_is_logged_in(self):
        self.assertTrue(self.client.login(username=self.superuser.username, password=u'test'))
        response = self.client.get(u'/')
        self.assertEqual(response.status_code, 200)
        self.assertTrue(response.wsgi_request.user, self.superuser)

    def test_admin_route_uses_the_admin_if_admin_is_logged_in(self):
        self.assertTrue(self.client.login(username=self.superuser.username, password=u'test'))
        response = self.client.get(u'/admin/')
        self.assertEqual(response.status_code, 200)
        self.assertTrue(response.wsgi_request.user, self.superuser)

    def test_public_route_uses_the_user_if_admin_is_logged_in_as_another_user(self):
        self.assertTrue(self.client.login(username=self.superuser.username, password=u'test'))
        self.client.get(u'/admin/{}/login-as/'.format(self.user.pk))
        response = self.client.get(u'/')
        self.assertEqual(response.status_code, 200)
        self.assertTrue(response.wsgi_request.user, self.user)

    def test_admin_route_uses_the_admin_if_admin_is_logged_in_as_another_user(self):
        self.assertTrue(self.client.login(username=self.superuser.username, password=u'test'))
        self.client.get(u'/admin/{}/login-as/'.format(self.user.pk))
        response = self.client.get(u'/admin/')
        self.assertEqual(response.status_code, 200)
        self.assertTrue(response.wsgi_request.user, self.superuser)
