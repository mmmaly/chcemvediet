# vim: expandtab
# -*- coding: utf-8 -*-
from django.conf import settings

# Default number of days the invitations are valid and the invited user may use them to register.
# Individual invitations may have their custom validity periods.
DEFAULT_VALIDITY = getattr(settings, u'INVITATIONS_DEFAULT_VALIDITY', 14)

# Whether the user may register with a valid invitation only, or the site is open to everybody.
INVITATION_ONLY = getattr(settings, u'INVITATIONS_INVITATION_ONLY', False)

# Whether existing users may send invitations, assuming their invitation supply is not empty.
# If False, the invitations may be sent from the admin interface only.
USERS_MAY_INVITE = getattr(settings, u'INVITATIONS_USERS_CAN_INVITE', True)

# Whether new users may send invitations imediatelly after being registered, or the right to send
# invitations must be enabled individually for every user.
NEW_USERS_MAY_INVITE = getattr(settings, u'INVITATIONS_NEW_USERS_MAY_INVITE', True)
