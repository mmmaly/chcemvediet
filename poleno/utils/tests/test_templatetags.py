# vim: expandtab
# -*- coding: utf-8 -*-
from django.template import Context, Template
from django.http import HttpResponse, HttpResponseNotFound
from django.conf import settings
from django.conf.urls import url, include
from django.conf.urls.i18n import i18n_patterns
from django.contrib.auth.models import User
from django.utils import timezone
from django.test import TestCase
from django.test.utils import override_settings

from poleno.utils.date import utc_datetime_from_local, local_datetime_from_local
from poleno.utils.misc import Bunch
from poleno.utils.translation import translation


class TemplatetagsStringTest(TestCase):
    u"""
    Tests ``subtract``, ``negate``, ``range``, ``utc_date``, ``local_date``, ``squeeze``,
    ``method``, ``call_with``, ``call`` and ``with`` template filters and ``lorem`` template tags.
    Tests are performed on simple templates in strings.
    """

    def _render(self, template, **context):
        return Template(template).render(Context(context))


    def test_substract_filter(self):
        u"""
        Tests ``number|subtract:number`` filter with constants, negative constants and variables.
        """
        rendered = self._render(
                u'{% load subtract from poleno.utils %}'
                u'({{ 64|subtract:3 }})' # constant numbers
                u'({{ b|subtract:a }})' # variables
                u'({{ -64|subtract:-43 }})' # negative numbers
                u'', a=47, b=23)
        self.assertEqual(rendered, u'(61)(-24)(-21)')

    def test_negate_filter(self):
        u"""
        Tests ``number|negate`` filter with constants, negative constants and variables.
        """
        rendered = self._render(
                u'{% load negate from poleno.utils %}'
                u'({{ -47|negate }})' # negative constant number
                u'({{ a|negate }})' # variable
                u'({{ 0|negate }})' # zero
                u'', a=33)
        self.assertEqual(rendered, u'(47)(-33)(0)')

    def test_range_filter(self):
        u"""
        Tests ``number|range:number`` filter with constants, variables, numbers, strings and empty
        intervals.
        """
        rendered = self._render(
                u'{% load range from poleno.utils %}'
                u'({% for x in -3|range:4 %}{{ x }},{% endfor %})' # constant numbers
                u'({% for x in "nop"|range:"2" %}{{ x }},{% endfor %})' # invalid argument
                u'({% for x in "-1"|range:"2" %}{{ x }},{% endfor %})' # constant strings
                u'({% for x in 4|range:b %}{{ x }},{% endfor %})' # variables
                u'({% for x in a|range:b %}{{ x }},{% endfor %})' # variables
                u'', a=3, b=u'4')
        self.assertEqual(rendered, u'(-3,-2,-1,0,1,2,3,)()(-1,0,1,)()(3,)')

    def test_utc_date_and_local_date_filters(self):
        u"""
        Tests ``datetime|utc_date`` and ``datetime|local_date`` filter. The filters are tested with
        datetimes in UTC, in local timezone and in some other explicitly set timezone. The filters
        are also tested with points in time respresenting different date in local timezone than in
        UTC.
        """
        with timezone.override(u'Europe/Bratislava'): # UTC +1
            # 2014-12-11 00:20:00 in Europe/Bratislava == 2014-12-10 23:20:00 UTC; Still yesterday in UTC
            utc = utc_datetime_from_local(2014, 12, 11, 0, 20, 0)
            local = local_datetime_from_local(2014, 12, 11, 0, 20, 0)
            rendered = self._render(
                    u'{% load utc_date local_date from poleno.utils %}'
                    u'({{ utc|utc_date|date:"Y-m-d" }})'
                    u'({{ local|utc_date|date:"Y-m-d" }})'
                    u'({{ utc|local_date|date:"Y-m-d" }})'
                    u'({{ local|local_date|date:"Y-m-d" }})'
                    u'', utc=utc, local=local)
            self.assertEqual(rendered, u'(2014-12-10)(2014-12-10)(2014-12-11)(2014-12-11)')

            # 2014-12-11 10:20:00 in Europe/Bratislava == 2014-12-11 09:20:00 UTC; The same day in UTC
            utc = utc_datetime_from_local(2014, 12, 11, 10, 20, 0)
            local = local_datetime_from_local(2014, 12, 11, 10, 20, 0)
            rendered = self._render(
                    u'{% load utc_date local_date from poleno.utils %}'
                    u'({{ utc|utc_date|date:"Y-m-d" }})'
                    u'({{ local|utc_date|date:"Y-m-d" }})'
                    u'({{ utc|local_date|date:"Y-m-d" }})'
                    u'({{ local|local_date|date:"Y-m-d" }})'
                    u'', utc=utc, local=local)
            self.assertEqual(rendered, u'(2014-12-11)(2014-12-11)(2014-12-11)(2014-12-11)')

        with timezone.override(u'America/Montreal'): # UTC -5
            # 2014-12-11 22:20:00 in America/Montreal == 2014-12-12 03:20:00 UTC; Already tomorrow in UTC
            utc = utc_datetime_from_local(2014, 12, 11, 22, 20, 0)
            local = local_datetime_from_local(2014, 12, 11, 22, 20, 0)
            rendered = self._render(
                    u'{% load utc_date local_date from poleno.utils %}'
                    u'({{ utc|utc_date|date:"Y-m-d" }})'
                    u'({{ local|utc_date|date:"Y-m-d" }})'
                    u'({{ utc|local_date|date:"Y-m-d" }})'
                    u'({{ local|local_date|date:"Y-m-d" }})'
                    u'', utc=utc, local=local)
            self.assertEqual(rendered, u'(2014-12-12)(2014-12-12)(2014-12-11)(2014-12-11)')

            # 2014-12-11 04:20:00 in Europe/Bratislava == 2014-12-11 03:20:00 UTC == 2014-12-10 22:20:00 in America/Montreal
            with timezone.override(u'Europe/Bratislava'): # UTC +1
                other = local_datetime_from_local(2014, 12, 11, 4, 20, 0)
                other_tz = timezone.get_current_timezone()
            rendered = self._render(
                    u'{% load utc_date local_date from poleno.utils %}'
                    u'({{ other|utc_date|date:"Y-m-d" }})'
                    u'({{ other|local_date|date:"Y-m-d" }})'
                    u'({{ other|local_date:other_tz|date:"Y-m-d" }})'
                    u'', other=other, other_tz=other_tz)
            self.assertEqual(rendered, u'(2014-12-11)(2014-12-10)(2014-12-11)')

    def test_squeeze_filter(self):
        u"""
        Tests ``text|squeeze`` filter with constants and variables and in a block context.
        """
        rendered = self._render(
                u'{% load squeeze from poleno.utils %}'
                u'({{ s|squeeze }})' # variable
                u'({{ "  f\tf   "|squeeze }})' # constant string
                u'({% filter squeeze %}\n\n\txxx    yyy\nzzz\n\n\n\r{% endfilter %})' # block context
                u'', s=u'  aaa\t\n\n bbb ccc\n\r\n')
        self.assertEqual(rendered, u'(aaa bbb ccc)(f f)(xxx yyy zzz)')

    def test_generic_type_filter(self):
        u"""
        Tests ``obj|generic_type|method`` filter calls the method.
        """
        user = User.objects.create_user(u'aaa')
        rendered = self._render(
                u'{% load generic_type method from poleno.utils %}'
                u'({{ user|generic_type|method:"app_label" }})'
                u'({{ user|generic_type|method:"model" }})'
                u'({{ user|generic_type|method:"name" }})'
                u'', user=user)
        self.assertEqual(rendered, u'(auth)(user)(user)')

    def test_call_method_filters(self):
        u"""
        Tests ``obj|method:"name"|arg:arg|call`` and ``obj|method:"name"|call_with:arg`` filters
        for calling object methods with arguments.
        """
        a = Bunch(plus=(lambda a, b: a + b))
        b = {'minus': (lambda a, b: a - b)}
        rendered = self._render(
                u'{% load method call_with call with from poleno.utils %}'
                u'({{ a|method:"plus"|with:10|with:11|call }})'
                u'({{ b|method:"minus"|with:5|call_with:10 }})'
                u'({{ a|method:"nop"|call_with:3 }})' # invalid method
                u'({{ b|method:"nop"|with:a|call }})' # invalid method
                u'', a=a, b=b)
        self.assertEqual(rendered, u'(21)(-5)([not callable])([not callable])')

    def test_lorem_tag(self):
        u"""
        Test ``lorem`` template tag.
        """
        rendered = self._render(
                u'{% load lorem from poleno.utils %}'
                u'({% lorem %})' # default text as plain text
                u'({% lorem 14 2 "p" %})' # random text as paragraphs
                u'')
        self.assertRegexpMatches(rendered, r'^\(Lorem ipsum .*\)\(<p>.{30,}</p>\s*<p>.{30,}</p>\)$')

class ActiveTemplatefilterTest(TestCase):
    u"""
    Tests ``active`` template filter.
    """
    def active_view(request):
        return HttpResponse(Template(
            u'{% load active from poleno.utils %}'
            u'(index={{ request|active:"index" }})'
            u'(first={{ request|active:"first" }})'
            u'(second={{ request|active:"second" }})'
            u'(second:first={{ request|active:"second:first" }})'
        ).render(Context({
            u'request': request,
        })))

    urlpatterns = [
        url(r'^$', active_view, name=u'index'),
        url(r'^first/', active_view, name=u'first'),
        url(r'^second/', include(([
            url(r'^$', active_view, name=u'index'),
            url(r'^first/', active_view, name=u'first'),
        ], None, u'second'))),
    ]

    urls = Bunch(
        urlpatterns=urlpatterns,
    )


    def test_active_filter(self):
        u"""
        Tests ``active`` filter by requesting a view using a template with this filter. Checking
        that only the current view and its subviews are marked as active.
        """
        r1 = self.client.get(u'/')
        r2 = self.client.get(u'/first/')
        r3 = self.client.get(u'/second/')
        r4 = self.client.get(u'/second/first/')

        for r in [r1, r2, r3, r4]:
            self.assertIs(type(r), HttpResponse)
            self.assertEqual(r.status_code, 200)

        # "index" is active for only "/"
        # "first" is active for only "/first/"
        # "second" is active for both "/second/" and "/second/first/"
        # "second:first" is active for only "/second/first/"
        self.assertEqual(r1.content, u'(index=True)(first=False)(second=False)(second:first=False)')
        self.assertEqual(r2.content, u'(index=False)(first=True)(second=False)(second:first=False)')
        self.assertEqual(r3.content, u'(index=False)(first=False)(second=True)(second:first=False)')
        self.assertEqual(r4.content, u'(index=False)(first=False)(second=True)(second:first=True)')

class ChangeLangTemplatetagTest(TestCase):
    u"""
    Tests ``change_lang`` template tag. Tests are performed by requesting view using template with
    this tag.
    """
    def language_view(request, *args, **kwargs):
        return HttpResponse(Template(
            u'{% load change_lang from poleno.utils %}'
            u'({% change_lang "en" %})'
            u'({% change_lang "de" %})'
            u'({% change_lang "fr" %})'
        ).render(Context({
            u'request': request,
        })))

    def page_not_found(request):
        return HttpResponseNotFound(Template(
            u'{% load change_lang from poleno.utils %}'
            u'({% change_lang "en" %})'
            u'({% change_lang "de" %})'
            u'({% change_lang "fr" %})'
        ).render(Context({
            u'request': request,
        })))

    urlpatterns = list(i18n_patterns(
        url(r'^language/$', language_view, name=u'language'),
        url(r'^kwargs/(?P<a>\d+)/(?P<b>\d+)/$', language_view, name=u'language_kwargs'),
        url(r'^args/(.+)/(.+)/(.+)/$', language_view, name=u'language_args'),
    ))

    urls = Bunch(
        urlpatterns=urlpatterns,
        handler404=page_not_found,
    )

    def _pre_setup(self):
        super(ChangeLangTemplatetagTest, self)._pre_setup()
        self.lang = ((u'de', u'Deutsch'), (u'en', u'English'), (u'fr', u'Francais'))
        self.settings_override = override_settings(
            LANGUAGES=self.lang,
            MIDDLEWARE_CLASSES=[mc for mc in settings.MIDDLEWARE_CLASSES
                                if mc != u'django.middleware.locale.LocaleMiddleware'],
            )
        self.settings_override.enable()

    def _post_teardown(self):
        self.settings_override.disable()
        super(ChangeLangTemplatetagTest, self)._post_teardown()


    def test_change_lang_tag(self):
        u"""
        Tests ``change_lang`` template tag by requesting a view using a template with this tag.
        Checking that it generates correct links to the same view in different languages.
        """
        for language, _ in self.lang:
            with translation(language):
                r = self.client.get(u'/{}/language/'.format(language))
                self.assertIs(type(r), HttpResponse)
                self.assertEqual(r.status_code, 200)
                self.assertEqual(r.content, u'(/en/language/)(/de/language/)(/fr/language/)')

    def test_change_lang_tag_with_missing_language_in_url(self):
        u"""
        Tests ``change_lang`` template tag without language prefix in URL. Checking that it
        generates same URLs, for all defined languages, if they are active or not.
        """
        for language, _ in self.lang:
            with translation(language):
                r = self.client.get(u'/language/')
                self.assertIs(type(r), HttpResponseNotFound)
                self.assertEqual(r.status_code, 404)
                self.assertEqual(r.content, u'(/language/)(/language/)(/language/)')

    def test_change_lang_tag_with_positional_arguments(self):
        r = self.client.get(u'/en/args/1/2/3/')
        self.assertIs(type(r), HttpResponse)
        self.assertEqual(r.status_code, 200)
        self.assertEqual(r.content, u'(/en/args/1/2/3/)(/de/args/1/2/3/)(/fr/args/1/2/3/)')

    def test_change_lang_tag_with_keyword_arguments(self):
        r = self.client.get(u'/en/kwargs/1/2/')
        self.assertIs(type(r), HttpResponse)
        self.assertEqual(r.status_code, 200)
        self.assertEqual(r.content, u'(/en/kwargs/1/2/)(/de/kwargs/1/2/)(/fr/kwargs/1/2/)')

class AmendTemplatetagTest(TestCase):
    u"""
    Tests ``amend`` and ``append`` template tags.
    """

    def _render(self, template, **context):
        return Template(template).render(Context(context))


    def test_prepend_tag(self):
        rendered = self._render(
                u'{% load amend prepend from poleno.amend %}'
                u'{% amend %}'
                u'  <ul>'
                u'    <li>aaa</li>'
                u'    <li>bbb</li>'
                u'  </ul>'
                u'  {% prepend path=".//ul" %}<li>xxx</li>{% endprepend %}'
                u'  {% prepend path=".//li" %}!{% endprepend %}'
                u'{% endamend %}'
                u'')
        self.assertHTMLEqual(rendered,
                u'<ul>'
                u'  <li>!xxx</li>'
                u'  <li>!aaa</li>'
                u'  <li>!bbb</li>'
                u'</ul>'
                u'')

    def test_append_tag(self):
        rendered = self._render(
                u'{% load amend append from poleno.amend %}'
                u'{% amend %}'
                u'  <ul>'
                u'    <li>aaa</li>'
                u'    <li>bbb</li>'
                u'  </ul>'
                u'  {% append path=".//ul" %}<li>xxx</li>{% endappend %}'
                u'  {% append path=".//li" %}!{% endappend %}'
                u'{% endamend %}'
                u'')
        self.assertHTMLEqual(rendered,
                u'<ul>'
                u'  <li>aaa!</li>'
                u'  <li>bbb!</li>'
                u'  <li>xxx!</li>'
                u'</ul>'
                u'')

    def test_before_tag(self):
        rendered = self._render(
                u'{% load amend before from poleno.amend %}'
                u'{% amend %}'
                u'  <ul>'
                u'    <li>aaa</li>'
                u'    <li>bbb</li>'
                u'    <li>ccc</li>'
                u'  </ul>'
                u'  {% before path=".//li[2]" %}<li>xxx</li>{% endbefore %}'
                u'{% endamend %}'
                u'')
        self.assertHTMLEqual(rendered,
                u'<ul>'
                u'  <li>aaa</li>'
                u'  <li>xxx</li>'
                u'  <li>bbb</li>'
                u'  <li>ccc</li>'
                u'</ul>'
                u'')

    def test_after_tag(self):
        rendered = self._render(
                u'{% load amend after from poleno.amend %}'
                u'{% amend %}'
                u'  <ul>'
                u'    <li>aaa</li>'
                u'    <li>bbb</li>'
                u'    <li>ccc</li>'
                u'  </ul>'
                u'  {% after path=".//li[2]" %}<li>xxx</li>{% endafter %}'
                u'{% endamend %}'
                u'')
        self.assertHTMLEqual(rendered,
                u'<ul>'
                u'  <li>aaa</li>'
                u'  <li>bbb</li>'
                u'  <li>xxx</li>'
                u'  <li>ccc</li>'
                u'</ul>'
                u'')

    def test_delete_tag(self):
        rendered = self._render(
                u'{% load amend delete from poleno.amend %}'
                u'{% amend %}'
                u'  <ul>'
                u'    <li>aaa</li>'
                u'    <li>bbb</li>'
                u'    <li>ccc</li>'
                u'  </ul>'
                u'  {% delete path=".//li[2]" %}'
                u'{% endamend %}'
                u'')
        self.assertHTMLEqual(rendered,
                u'<ul>'
                u'  <li>aaa</li>'
                u'  <li>ccc</li>'
                u'</ul>'
                u'')

    def test_set_attributes_tag(self):
        rendered = self._render(
                u'{% load amend set_attributes from poleno.amend %}'
                u'{% amend %}'
                u'  <ul>'
                u'    <li aaa="foo">xxx</li>'
                u'    <li aaa="foo">xxx</li>'
                u'    <li aaa="foo">xxx</li>'
                u'    <li aaa="foo">xxx</li>'
                u'    <li aaa="foo">xxx</li>'
                u'  </ul>'
                u'  {% set_attributes path=".//li[1]" aaa=None bbb=None %}'
                u'  {% set_attributes path=".//li[2]" aaa=False bbb=False %}'
                u'  {% set_attributes path=".//li[3]" aaa=True bbb=True %}'
                u'  {% set_attributes path=".//li[4]" aaa="bar" bbb="baz" ccc="" %}'
                u'  {% set_attributes path=".//li[5]" aaa=1 bbb=2 ccc=0 %}'
                u'{% endamend %}'
                u'')
        self.assertHTMLEqual(rendered,
                u'<ul>'
                u'  <li>xxx</li>'
                u'  <li>xxx</li>'
                u'  <li aaa bbb>xxx</li>'
                u'  <li aaa="bar" bbb="baz" ccc="">xxx</li>'
                u'  <li aaa="1" bbb="2" ccc="0">xxx</li>'
                u'</ul>'
                u'')

    def test_amend_tag_with_operation_tags_before_content(self):
        rendered = self._render(
                u'{% load amend prepend from poleno.amend %}'
                u'{% amend %}'
                u'  {% prepend path=".//ul" %}<li>xxx</li>{% endprepend %}'
                u'  {% prepend path=".//li" %}!{% endprepend %}'
                u'  <ul>'
                u'    <li>aaa</li>'
                u'    <li>bbb</li>'
                u'  </ul>'
                u'{% endamend %}'
                u'')
        self.assertHTMLEqual(rendered,
                u'<ul>'
                u'  <li>!xxx</li>'
                u'  <li>!aaa</li>'
                u'  <li>!bbb</li>'
                u'</ul>'
                u'')

    def test_amend_tag_on_plain_text(self):
        rendered = self._render(
                u'{% load amend prepend append from poleno.amend %}'
                u'{% amend %}'
                u'  aaa bbb ccc'
                u'  {% prepend path="." %}xxx{% endprepend %}'
                u'  {% append path="." %}yyy{% endappend %}'
                u'{% endamend %}'
                u'')
        self.assertHTMLEqual(rendered, u'xxx aaa bbb ccc yyy')

    def test_amend_tag_on_multiple_tags(self):
        rendered = self._render(
                u'{% load amend prepend append from poleno.amend %}'
                u'{% amend %}'
                u'  <p>aaa</p>'
                u'  <p>bbb</p>'
                u'  <p>ccc</p>'
                u'  {% prepend path="." %}<p>xxx</p>{% endprepend %}'
                u'  {% append path="." %}<p>yyy</p>{% endappend %}'
                u'{% endamend %}'
                u'')
        self.assertHTMLEqual(rendered,
                u'<p>xxx</p>'
                u'<p>aaa</p>'
                u'<p>bbb</p>'
                u'<p>ccc</p>'
                u'<p>yyy</p>'
                u'')

    def test_amend_tag_on_imported_content(self):
        rendered = self._render(
                u'{% load amend from poleno.amend %}'
                u'{% amend %}'
                u'  {% include "utils/tests/amendtemplatetagtest/test_amend_tag_on_imported_content.html" %}'
                u'{% endamend %}'
                u'')
        self.assertHTMLEqual(rendered,
                u'<ul>'
                u'  <li>!xxx</li>'
                u'  <li>!aaa</li>'
                u'  <li>!bbb</li>'
                u'</ul>'
                u'')

    def test_multiple_amend_tags(self):
        rendered = self._render(
                u'{% load amend prepend append from poleno.amend %}'
                u'{% amend %}'
                u'  <ul>'
                u'    <li>aaa</li>'
                u'    <li>bbb</li>'
                u'  </ul>'
                u'  {% prepend path=".//ul" %}<li>xxx</li>{% endprepend %}'
                u'  {% prepend path=".//li" %}!{% endprepend %}'
                u'{% endamend %}'
                u'{% amend %}'
                u'  <ul>'
                u'    <li>aaa</li>'
                u'    <li>bbb</li>'
                u'  </ul>'
                u'  {% append path=".//ul" %}<li>xxx</li>{% endappend %}'
                u'  {% append path=".//li" %}!{% endappend %}'
                u'{% endamend %}'
                u'')
        self.assertHTMLEqual(rendered,
                u'<ul>'
                u'  <li>!xxx</li>'
                u'  <li>!aaa</li>'
                u'  <li>!bbb</li>'
                u'</ul>'
                u'<ul>'
                u'  <li>aaa!</li>'
                u'  <li>bbb!</li>'
                u'  <li>xxx!</li>'
                u'</ul>'
                u'')

    def test_nested_amend_tags(self):
        rendered = self._render(
                u'{% load amend prepend append from poleno.amend %}'
                u'{% amend %}'
                u'  <ul>'
                u'    <li>aaa</li>'
                u'    <li>bbb</li>'
                u'    <li>'
                u'      {% amend %}'
                u'        <ul>'
                u'          <li>aaa</li>'
                u'          <li>bbb</li>'
                u'        </ul>'
                u'        {% append path=".//ul" %}<li>yyy</li>{% endappend %}'
                u'        {% append path=".//li" %}?{% endappend %}'
                u'      {% endamend %}'
                u'    </li>'
                u'  </ul>'
                u'  {% prepend path=".//ul" %}<li>xxx</li>{% endprepend %}'
                u'  {% prepend path=".//li" %}!{% endprepend %}'
                u'{% endamend %}'
                u'')
        self.assertHTMLEqual(rendered,
                u'<ul>'
                u'  <li>!xxx</li>'
                u'  <li>!aaa</li>'
                u'  <li>!bbb</li>'
                u'  <li>!'
                u'    <ul>'
                u'      <li>!xxx</li>'
                u'      <li>!aaa?</li>'
                u'      <li>!bbb?</li>'
                u'      <li>!yyy?</li>'
                u'    </ul>'
                u'  </li>'
                u'</ul>'
                u'')

    def test_nested_amend_tags_with_operation_tags_before_content(self):
        rendered = self._render(
                u'{% load amend prepend append from poleno.amend %}'
                u'{% amend %}'
                u'  {% prepend path=".//ul" %}<li>xxx</li>{% endprepend %}'
                u'  {% prepend path=".//li" %}!{% endprepend %}'
                u'  <ul>'
                u'    <li>aaa</li>'
                u'    <li>bbb</li>'
                u'    <li>'
                u'      {% amend %}'
                u'        {% append path=".//ul" %}<li>yyy</li>{% endappend %}'
                u'        {% append path=".//li" %}?{% endappend %}'
                u'        <ul>'
                u'          <li>aaa</li>'
                u'          <li>bbb</li>'
                u'        </ul>'
                u'      {% endamend %}'
                u'    </li>'
                u'  </ul>'
                u'{% endamend %}'
                u'')
        self.assertHTMLEqual(rendered,
                u'<ul>'
                u'  <li>!xxx</li>'
                u'  <li>!aaa</li>'
                u'  <li>!bbb</li>'
                u'  <li>!'
                u'    <ul>'
                u'      <li>!xxx</li>'
                u'      <li>!aaa?</li>'
                u'      <li>!bbb?</li>'
                u'      <li>!yyy?</li>'
                u'    </ul>'
                u'  </li>'
                u'</ul>'
                u'')

    def test_without_amend_tag(self):
        rendered = self._render(
                u'{% load prepend append before after delete set_attributes from poleno.amend %}'
                u'<ul>'
                u'  <li>aaa</li>'
                u'  <li>bbb</li>'
                u'</ul>'
                u'<p>foobar</p>'
                u'{% prepend path=".//ul" %}<li>ccc</li>{% endprepend %}'
                u'{% append path=".//ul" %}<li>ddd</li>{% endappend %}'
                u'{% before path=".//li[2]" %}<li>eee</li>{% endbefore %}'
                u'{% after path=".//li[2]" %}<li>fff</li>{% endafter %}'
                u'{% delete path=".//p" %}'
                u'{% set_attributes path=".//ul" att=True %}'
                u'')
        self.assertHTMLEqual(rendered,
                u'<ul>'
                u'  <li>aaa</li>'
                u'  <li>bbb</li>'
                u'</ul>'
                u'<p>foobar</p>'
                u'')
