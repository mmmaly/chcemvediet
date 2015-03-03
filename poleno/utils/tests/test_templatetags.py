# vim: expandtab
# -*- coding: utf-8 -*-
import re

from django.template import Context, Template
from django.http import HttpResponse
from django.conf.urls import patterns, url, include
from django.conf.urls.i18n import i18n_patterns
from django.contrib.auth.models import User
from django.utils import timezone
from django.test import TestCase

from poleno.utils.date import utc_datetime_from_local, local_datetime_from_local
from poleno.utils.misc import Bunch


class TemplatetagsStringTest(TestCase):
    u"""
    Tests ``subtract``, ``negate``, ``range``, ``utc_date``, ``local_date``, ``squeeze``,
    ``method``, ``call_with``, ``call`` and ``with`` template filters and ``lorem``,
    ``external_css`` and ``external_js`` template tags. Tests are performed on simple templates in
    strings.
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

    def test_external_css_and_js_tags(self):
        u"""
        Test that ``external_css`` and ``external_js`` template tags render exactly all external
        css and js assets confifured in ``settings.EXTERNAL_CSS`` and ``settings.EXTERNAL_JS`` in
        the same order as configured.
        """
        css = [u'//test/aaa.css', u'//test/bbb.css']
        js = [u'//test/ccc.js']
        with self.settings(EXTERNAL_CSS=css, EXTERNAL_JS=js):
            rendered = self._render(
                    u'{% load external_css external_js from poleno.utils %}'
                    u'{% external_css %}{% external_js %}'
                    u'')

            found_css = re.findall(r'<link .*?href="(.*?)".*?>', rendered)
            self.assertEqual(found_css, css)

            found_js = re.findall(r'<script .*?src="(.*?)".*?>', rendered)
            self.assertEqual(found_js, js)

class TemplatetagsViewTest(TestCase):
    u"""
    Tests ``active`` template filter and ``change_lang`` template tag. Tests are performed by
    requesting views using templates with these filters and tags.
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

    def language_view(request):
        return HttpResponse(Template(
            u'{% load change_lang from poleno.utils %}'
            u'({% change_lang "en" %})'
            u'({% change_lang "de" %})'
            u'({% change_lang "fr" %})'
        ).render(Context({
            u'request': request,
        })))

    urls = tuple(patterns(u'',
        url(r'^$', active_view, name=u'index'),
        url(r'^first/', active_view, name=u'first'),
        url(r'^second/', include(namespace=u'second', arg=patterns(u'',
            url(r'^$', active_view, name=u'index'),
            url(r'^first/', active_view, name=u'first'),
        ))),
    ))
    urls += tuple(i18n_patterns(u'',
        url(r'^language/', language_view, name=u'language'),
    ))


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

    def test_change_lang_tag(self):
        u"""
        Tests ``change_lang`` template tag by requesting a view using a template with this tag.
        Checking that it generates corrent links to the same view in different languages.
        """
        lang = ((u'de', u'Deutsch'), ('en', u'English'), ('fr', u'Francais'))
        with self.settings(LANGUAGES=lang): # Fix active languages
            r1 = self.client.get(u'/en/language/')
            r2 = self.client.get(u'/de/language/')
            r3 = self.client.get(u'/fr/language/')

            for r in [r1, r2, r3]:
                self.assertIs(type(r), HttpResponse)
                self.assertEqual(r.status_code, 200)

            self.assertEqual(r1.content, u'(/en/language/)(/de/language/)(/fr/language/)')
            self.assertEqual(r2.content, u'(/en/language/)(/de/language/)(/fr/language/)')
            self.assertEqual(r3.content, u'(/en/language/)(/de/language/)(/fr/language/)')
