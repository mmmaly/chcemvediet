from django.conf import settings
from django.core.paginator import Paginator
from django.contrib.sitemaps import Sitemap
from django.utils.http import urlencode

from poleno.utils.urls import reverse
from poleno.utils.translation import translation

from .constants import OBLIGEES_PER_PAGE
from .models import Obligee


class ObligeesSitemap(Sitemap):
    changefreq = u'weekly'
    priority = 0.3

    def items(self):
        obligees = Obligee.objects.pending().order_by_name()
        paginator = Paginator(obligees, OBLIGEES_PER_PAGE)
        return [(lang, i) for lang, name in settings.LANGUAGES for i in paginator.page_range]

    def location(self, item):
        lang, i = item
        with translation(lang):
            return reverse(u'obligees:index') + u'?' + urlencode({u'page': i})
