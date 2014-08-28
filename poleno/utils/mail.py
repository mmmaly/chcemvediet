# vim: expandtab
# -*- coding: utf-8 -*-
import re

def mail_address_with_name(name, address):
    u"""
    To/From e-mail headers may contain sender's/recepient's name alongside his e-mail address. To
    prevent any unexpected e-mail behaviour, we filter all special characters from the ``name``
    part. Moreover we merge all consecutive whitespace into a single spaces. This will remove all
    line breaks as well. We assume that ``address`` is a valid e-mail address and do not check it.
    It must be validated before calling this function.

    The following characters are special according to RFC-822:
        ( ) < > @ , ; : \\ " . [ ]
    See: https://www.ietf.org/rfc/rfc0822.txt

    Examples:
        name: "John Down", address: "john.down@example.com"  ->  "John Down <john.down@example.com>"
        name: "<bad@name.com>,", address: "john.down@example.com" -> "bad name com <john.down@example.com>"
    """
    name = re.sub(r'[()<>@,;:\\".\[\]\s]+', ' ', name, flags=re.U).strip()
    return u'%s <%s>' % (name, address)

