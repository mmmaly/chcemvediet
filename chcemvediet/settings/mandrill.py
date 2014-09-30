# vim: expandtab
# -*- coding: utf-8 -*-

INSTALLED_APPS += (
    u'djrill',
)

# Force Djrill to use HTTPS for API calls. By default it uses HTTP.
MANDRILL_API_URL = u'https://mandrillapp.com/api/1.0'

# FIXME: Djrill sends the mail synchronously during user request. It would be better to just
# prepare the mail during the request and send it asynchronously from a cron job. So the mail is
# delivered even if Mandrill is unreachable for a while, and the user request is not blocked while
# waiting for Mandrill to response.
EMAIL_BACKEND = u'djrill.mail.backends.djrill.DjrillBackend'
