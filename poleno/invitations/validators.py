# vim: expandtab
# -*- coding: utf-8 -*-
from email.utils import getaddresses

from django.core.exceptions import ValidationError
from django.db.models import Q
from django.utils.translation import ugettext_lazy as _
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
        raise ValidationError(_(u'invitations:validate_unused_emails:one {0}').format(used[0]))
    elif len(used) < 5:
        raise ValidationError(_(u'invitations:validate_unused_emails:few {0} {1}').format(u', '.join(used[:-1]), used[-1]))
    else:
        raise ValidationError(_(u'invitations:validate_unused_emails:many {0}').format(u', '.join(used[:4])))
