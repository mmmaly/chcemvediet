# vim: expandtab
# -*- coding: utf-8 -*-
from email.utils import getaddresses

from django.core.exceptions import ValidationError
from django.db.models import Q
from django.contrib.auth.models import User
from allauth.account.models import EmailAddress

def validate_unused_emails(value):
    q = Q()
    for name, email in getaddresses([value]):
        q |= Q(email__iexact=email)

    used = sorted(set(o.email
            for m in [User, EmailAddress]
            for o in m.objects.filter(q)[:5]
            ))

    if len(used) == 0:
        return
    elif len(used) == 1:
        raise ValidationError(u'E-mail {0} is already registered.'.format(used[0]))
    elif len(used) < 5:
        raise ValidationError(u'E-mails {0} and {1} are already registered.'.format(u', '.join(used[:-1]), used[-1]))
    else:
        raise ValidationError(u'E-mails {0} and some other e-mails already registered.'.format(u', '.join(used[:4])))
