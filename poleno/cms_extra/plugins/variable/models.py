# vim: expandtab

from django.utils.translation import ugettext_lazy as _
from django.db.models import TextField
from django.utils.text import Truncator
from cms.models import CMSPlugin

class Variable(CMSPlugin):
    content = TextField(verbose_name=_("content"))

    def __unicode__(self):
        return Truncator(self.content).chars(30)

