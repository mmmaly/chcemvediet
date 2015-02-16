# vim: expandtab
# -*- coding: utf-8 -*-
import random
import json

from django.core.urlresolvers import reverse
from django.http import JsonResponse
from django.test import TestCase

from poleno.utils.test import ViewTestCaseMixin

from . import ObligeesTestCaseMixin
from ..models import Obligee

class IndexViewTest(ObligeesTestCaseMixin, ViewTestCaseMixin, TestCase):
    u"""
    Tests ``index()`` view registered as "obligees:index".
    """

    def test_allowed_http_methods(self):
        allowed = [u'HEAD', u'GET']
        self.assert_allowed_http_methods(allowed, reverse(u'obligees:index'))

    def test_obligees_index(self):
        response = self.client.get(reverse(u'obligees:index'))
        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, u'obligees/index.html')

    def test_paginator_with_no_page_number_shows_first_page(self):
        oblgs = [self._create_obligee() for i in range(51)]
        response = self.client.get(reverse(u'obligees:index'))
        self.assertEqual(response.status_code, 200)
        self.assertEqual(repr(response.context[u'obligee_page']), u'<Page 1 of 3>')
        self.assertEqual(list(response.context[u'obligee_page']), oblgs[:25])

    def test_paginator_with_valid_page_number_shows_requested_page(self):
        oblgs = [self._create_obligee() for i in range(51)]
        response = self.client.get(reverse(u'obligees:index') + u'?page=2')
        self.assertEqual(response.status_code, 200)
        self.assertEqual(repr(response.context[u'obligee_page']), u'<Page 2 of 3>')
        self.assertEqual(list(response.context[u'obligee_page']), oblgs[25:50])

    def test_paginator_with_too_high_page_number_shows_last_page(self):
        oblgs = [self._create_obligee() for i in range(51)]
        response = self.client.get(reverse(u'obligees:index') + u'?page=47')
        self.assertEqual(response.status_code, 200)
        self.assertEqual(repr(response.context[u'obligee_page']), u'<Page 3 of 3>')
        self.assertEqual(list(response.context[u'obligee_page']), oblgs[50:])

    def test_paginator_with_invalid_page_number_shows_first_page(self):
        oblgs = [self._create_obligee() for i in range(51)]
        response = self.client.get(reverse(u'obligees:index') + u'?page=invalid')
        self.assertEqual(response.status_code, 200)
        self.assertEqual(repr(response.context[u'obligee_page']), u'<Page 1 of 3>')
        self.assertEqual(list(response.context[u'obligee_page']), oblgs[:25])

    def test_paginator_with_no_obligees(self):
        response = self.client.get(reverse(u'obligees:index'))
        self.assertEqual(response.status_code, 200)
        self.assertEqual(repr(response.context[u'obligee_page']), u'<Page 1 of 1>')
        self.assertEqual(list(response.context[u'obligee_page']), [])

class AutocompleteViewTest(ObligeesTestCaseMixin, ViewTestCaseMixin, TestCase):
    u"""
    Tests ``autocomplete()`` view registered as "obligees:autocomplete".
    """

    def test_allowed_http_methods(self):
        allowed = [u'HEAD', u'GET']
        self.assert_allowed_http_methods(allowed, reverse(u'obligees:autocomplete'))

    def test_autocomplete_returns_json_with_correct_structure(self):
        oblg1 = self._create_obligee(name=u'Agency', street=u'Westend', city=u'Winterfield', zip=u'12345', emails=u'agency@a.com')
        oblg2 = self._create_obligee(name=u'Ministry', street=u'Eastend', city=u'Springfield', zip=u'12345', emails=u'ministry@a.com')
        response = self.client.get(reverse(u'obligees:autocomplete'))
        self.assertEqual(response.status_code, 200)
        self.assertIsInstance(response, JsonResponse)
        data = json.loads(response.content)
        self.assertEqual(data, [
                {
                u'label': u'Agency',
                u'obligee': {
                    u'id': oblg1.pk,
                    u'name': u'Agency',
                    u'street': u'Westend',
                    u'city': u'Winterfield',
                    u'zip': u'12345',
                    u'emails': u'agency@a.com',
                    u'slug': u'-agency-',
                    u'status': Obligee.STATUSES.PENDING,
                    },
                },
                {
                u'label': u'Ministry',
                u'obligee': {
                    u'id': oblg2.pk,
                    u'name': u'Ministry',
                    u'street': u'Eastend',
                    u'city': u'Springfield',
                    u'zip': u'12345',
                    u'emails': u'ministry@a.com',
                    u'slug': u'-ministry-',
                    u'status': Obligee.STATUSES.PENDING,
                    },
                },
            ])

    def test_autocomplete_is_case_insensitive(self):
        names = [u'aaa', u'AAA', u'AaA', u'ddd', u'Ddd', u'eee']
        oblgs = [self._create_obligee(name=n) for n in names]
        response = self.client.get(reverse(u'obligees:autocomplete') + u'?term=aAa')
        self.assertEqual(response.status_code, 200)
        data = json.loads(response.content)
        found = [d[u'obligee'][u'name'] for d in data]
        self.assertItemsEqual(found, [u'aaa', u'AAA', u'AaA'])

    def test_autocomplete_ignores_accents(self):
        names = [u'aáá', u'aää', u'aÁÄ', u'aaa', u'ddd', u'eee']
        oblgs = [self._create_obligee(name=n) for n in names]
        response = self.client.get(reverse(u'obligees:autocomplete') + u'?term=ǎaa')
        self.assertEqual(response.status_code, 200)
        data = json.loads(response.content)
        found = [d[u'obligee'][u'name'] for d in data]
        self.assertItemsEqual(found, [u'aáá', u'aää', u'aÁÄ', u'aaa'])

    def test_autocomplete_with_multiple_words(self):
        names = [u'aaa bbb ccc', u'bbb aaa', u'aaa ccc', u'ddd']
        oblgs = [self._create_obligee(name=n) for n in names]
        response = self.client.get(reverse(u'obligees:autocomplete') + u'?term=++aaa++bbb,ccc++,,++')
        self.assertEqual(response.status_code, 200)
        data = json.loads(response.content)
        found = [d[u'obligee'][u'name'] for d in data]
        self.assertItemsEqual(found, [u'aaa bbb ccc'])

    def test_autocomplete_matches_obligee_name_prefixes(self):
        names = [u'aa', u'aaa', u'aaaaaaa', u'aaaxxxx', u'xxxxaaa', u'xxxxaaaxxxx', u'xxx aaa', u'xxx aaax xxx']
        oblgs = [self._create_obligee(name=n) for n in names]
        response = self.client.get(reverse(u'obligees:autocomplete') + u'?term=aaa')
        self.assertEqual(response.status_code, 200)
        data = json.loads(response.content)
        found = [d[u'obligee'][u'name'] for d in data]
        self.assertItemsEqual(found, [u'aaa', u'aaaaaaa', u'aaaxxxx', u'xxx aaa', u'xxx aaax xxx'])

    def test_autocomplete_without_term_returns_everything(self):
        names = [u'aaa', u'bbb', u'ccc', u'ddd']
        oblgs = [self._create_obligee(name=n) for n in names]
        response = self.client.get(reverse(u'obligees:autocomplete'))
        self.assertEqual(response.status_code, 200)
        data = json.loads(response.content)
        found = [d[u'obligee'][u'name'] for d in data]
        self.assertItemsEqual(found, [u'aaa', u'bbb', u'ccc', u'ddd'])

    def test_autocomplete_returns_only_pending_obligees(self):
        oblg1 = self._create_obligee(name=u'aaa 1', status=Obligee.STATUSES.PENDING)
        oblg2 = self._create_obligee(name=u'aaa 2', status=Obligee.STATUSES.PENDING)
        oblg3 = self._create_obligee(name=u'aaa 3', status=Obligee.STATUSES.DISSOLVED)
        oblg4 = self._create_obligee(name=u'aaa 4', status=Obligee.STATUSES.DISSOLVED)
        response = self.client.get(reverse(u'obligees:autocomplete') + u'?term=aaa')
        self.assertEqual(response.status_code, 200)
        data = json.loads(response.content)
        found = [d[u'obligee'][u'name'] for d in data]
        self.assertItemsEqual(found, [u'aaa 1', u'aaa 2'])

    def test_autocomplete_returns_at_most_10_obligees(self):
        oblgs = [self._create_obligee(name=u'aaa %02d' % i) for i in range(25)]
        response = self.client.get(reverse(u'obligees:autocomplete') + u'?term=aaa')
        self.assertEqual(response.status_code, 200)
        data = json.loads(response.content)
        self.assertEqual(len(data), 10)

    def test_autocomplete_returns_obligees_ordered_by_name(self):
        names = [u'aaa', u'aaa bbb1', u'aaa bbb2', u'aaa ccc', u'aaa ddd', u'eee aaa', u'fff', u'ggg aaa', u'hhh']
        random.shuffle(names)
        oblgs = [self._create_obligee(name=n) for n in names]
        response = self.client.get(reverse(u'obligees:autocomplete') + u'?term=aaa')
        self.assertEqual(response.status_code, 200)
        data = json.loads(response.content)
        found = [d[u'obligee'][u'name'] for d in data]
        self.assertEqual(found, [u'aaa', u'aaa bbb1', u'aaa bbb2', u'aaa ccc', u'aaa ddd', u'eee aaa', u'ggg aaa'])

    def test_autocomplete_with_no_obligees(self):
        response = self.client.get(reverse(u'obligees:autocomplete') + u'?term=aaa')
        self.assertEqual(response.status_code, 200)
        data = json.loads(response.content)
        self.assertEqual(data, [])
