from allauth.account.auth_backends import AuthenticationBackend
from django.contrib.auth.backends import ModelBackend


# Logging in as another user is done by ``poleno.utils.admin_login_as.AdminLoginAsMiddleware``. The
# backends keep their names because existing sessions store the backend path.

class DjangoModelBackendWithAdminLoginAs(ModelBackend):
    pass

class AllauthAuthenticationBackendWithAdminLoginAs(AuthenticationBackend):
    pass
