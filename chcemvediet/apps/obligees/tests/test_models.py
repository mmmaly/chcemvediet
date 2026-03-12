# vim: expandtab
# -*- coding: utf-8 -*-
import random

from django.core.exceptions import ValidationError
from django.db import IntegrityError
from django.test import TestCase
from django.utils.translation import gettext as _

from chcemvediet.tests import ChcemvedietTestCaseMixin

from ..models import Obligee, HistoricalObligee


class ObligeeModelTest(ChcemvedietTestCaseMixin, TestCase):
    u"""
    Tests ``Obligee`` and ``HistoricalObligee`` models.
    """

    def test_official_name_field(self):
        oblg = self._create_obligee(official_name=u'Agency Official')
        self.assertEqual(oblg.official_name, u'Agency Official')

    def test_official_name_field_default_value_if_omitted(self):
        oblg = self._create_obligee(omit=[u'official_name'])
        self.assertEqual(oblg.official_name, u'')

    def test_name_field(self):
        oblg = self._create_obligee(name=u'Agency')
        self.assertEqual(oblg.name, u'Agency')

    def test_name_field_default_value_if_omitted(self):
        oblg = self._create_obligee(omit=[u'name'])
        self.assertEqual(oblg.name, u'')

    def test_name_field_must_be_unique(self):
        with self.assertRaisesMessage(IntegrityError, u'UNIQUE constraint failed: obligees_obligee.slug'):
            self._create_obligee(name=u'Agency')
            self._create_obligee(name=u'Agency')

    def test_slug_field_computed_value(self):
        oblg = self._create_obligee(name=u'Agency')
        self.assertEqual(oblg.slug, u'agency')

    def test_slug_field_computed_value_from_multiword_name(self):
        oblg = self._create_obligee(name=u'Some Important Agency')
        self.assertEqual(oblg.slug, u'some-important-agency')

    def test_slug_field_computed_value_from_name_with_accents(self):
        oblg = self._create_obligee(name=u'áäčďéěíľĺňóôŕřšťúýž')
        self.assertEqual(oblg.slug, u'aacdeeillnoorrstuyz')

    def test_slug_field_computed_value_from_name_with_uppercase_accents(self):
        oblg = self._create_obligee(name=u'ÁÄČĎÉĚÍĽĹŇÓÔŔŘŠŤÚÝŽ')
        self.assertEqual(oblg.slug, u'aacdeeillnoorrstuyz')

    def test_slug_field_computed_value_from_name_with_cyrillics(self):
        oblg = self._create_obligee(name=u'кюм иреуры рэпудёандаэ')
        self.assertEqual(oblg.slug, u'kium-ireury-repudioandae')

    def test_slug_field_computed_value_from_empty_name(self):
        oblg = self._create_obligee(name=u'')
        self.assertEqual(oblg.slug, u'')

    def test_slug_field_may_not_be_set_by_user(self):
        oblg = self._create_obligee(name=u'Agency', slug=u'-slug-')
        self.assertEqual(oblg.slug, u'agency')

    def test_slug_field_may_not_be_changed_by_user(self):
        oblg = self._create_obligee(name=u'Agency')
        oblg.slug = u'slug'
        oblg.save()
        self.assertEqual(oblg.slug, u'agency')
        oblg = Obligee.objects.get(pk=oblg.pk)
        self.assertEqual(oblg.slug, u'agency')

    def test_slug_field_is_changed_when_name_field_changes(self):
        oblg = self._create_obligee(name=u'Agency')
        oblg.name = u'Another Agency'
        oblg.save()
        self.assertEqual(oblg.slug, u'another-agency')
        oblg = Obligee.objects.get(pk=oblg.pk)
        self.assertEqual(oblg.slug, u'another-agency')

    def test_slug_field_is_not_changed_if_name_is_not_saved(self):
        oblg = self._create_obligee(name=u'Agency')
        oblg.name = u'Another Agency'
        oblg.save(update_fields=[u'street'])
        self.assertEqual(oblg.slug, u'agency')
        oblg = Obligee.objects.get(pk=oblg.pk)
        self.assertEqual(oblg.slug, u'agency')

    def test_slug_field_is_changed_if_name_is_saved(self):
        oblg = self._create_obligee(name=u'Agency')
        oblg.name = u'Another Agency'
        oblg.save(update_fields=[u'name'])
        self.assertEqual(oblg.slug, u'another-agency')
        oblg = Obligee.objects.get(pk=oblg.pk)
        self.assertEqual(oblg.slug, u'another-agency')

    def test_name_genitive_field(self):
        oblg = self._create_obligee(name_genitive=u'Agency genitive')
        self.assertEqual(oblg.name_genitive, u'Agency genitive')

    def test_name_genitive_field_default_value_if_omitted(self):
        oblg = self._create_obligee(omit=[u'name_genitive'])
        self.assertEqual(oblg.name_genitive, u'')

    def test_name_dative_field(self):
        oblg = self._create_obligee(name_dative=u'Agency dative')
        self.assertEqual(oblg.name_dative, u'Agency dative')

    def test_name_dative_field_default_value_if_omitted(self):
        oblg = self._create_obligee(omit=[u'name_dative'])
        self.assertEqual(oblg.name_dative, u'')

    def test_name_accusative_field(self):
        oblg = self._create_obligee(name_accusative=u'Agency accusative')
        self.assertEqual(oblg.name_accusative, u'Agency accusative')

    def test_name_accusative_field_default_value_if_omitted(self):
        oblg = self._create_obligee(omit=[u'name_accusative'])
        self.assertEqual(oblg.name_accusative, u'')

    def test_name_locative_field(self):
        oblg = self._create_obligee(name_locative=u'Agency locative')
        self.assertEqual(oblg.name_locative, u'Agency locative')

    def test_name_locative_field_default_value_if_omitted(self):
        oblg = self._create_obligee(omit=[u'name_locative'])
        self.assertEqual(oblg.name_locative, u'')

    def test_name_instrumental_field(self):
        oblg = self._create_obligee(name_instrumental=u'Agency instrumental')
        self.assertEqual(oblg.name_instrumental, u'Agency instrumental')

    def test_name_instrumental_field_default_value_if_omitted(self):
        oblg = self._create_obligee(omit=[u'name_instrumental'])
        self.assertEqual(oblg.name_instrumental, u'')

    def test_gender_field(self):
        tests = (
                (Obligee.GENDERS.MASCULINE, _(u'obligees:Obligee:gender:MASCULINE')),
                (Obligee.GENDERS.FEMININE, _(u'obligees:Obligee:gender:FEMININE')),
                (Obligee.GENDERS.NEUTER, _(u'obligees:Obligee:gender:NEUTER')),
                (Obligee.GENDERS.PLURALE, _(u'obligees:Obligee:gender:PLURALE')),
                )
        # Make sure we are testing all obligee genders
        tested_genders = [a for a, __ in tests]
        defined_genders = Obligee.GENDERS._inverse.keys()
        self.assertItemsEqual(tested_genders, defined_genders)

        for gender, expected_display in tests:
            oblg = self._create_obligee(gender=gender)
            self.assertEqual(oblg.gender, gender)
            self.assertEqual(oblg.get_gender_display(), expected_display)

    def test_gender_field_may_not_be_omitted(self):
        with self.assertRaisesMessage(IntegrityError, u'NOT NULL constraint failed: obligees_obligee.gender'):
            self._create_obligee(omit=[u'gender'])

    def test_ico_field(self):
        oblg = self._create_obligee(ico=u'12345678')
        self.assertEqual(oblg.ico, u'12345678')

    def test_ico_field_default_value_if_omitted(self):
        oblg = self._create_obligee(omit=[u'ico'])
        self.assertEqual(oblg.ico, u'')

    def test_street_field(self):
        oblg = self._create_obligee(street=u'123 Westside')
        self.assertEqual(oblg.street, u'123 Westside')

    def test_street_field_default_value_if_omitted(self):
        oblg = self._create_obligee(omit=[u'street'])
        self.assertEqual(oblg.street, u'')

    def test_city_field(self):
        oblg = self._create_obligee(city=u'Winterfield')
        self.assertEqual(oblg.city, u'Winterfield')

    def test_city_field_default_value_if_omitted(self):
        oblg = self._create_obligee(omit=[u'city'])
        self.assertEqual(oblg.city, u'')

    def test_zip_field(self):
        oblg = self._create_obligee(zip=u'12345')
        self.assertEqual(oblg.zip, u'12345')

    def test_zip_field_default_value_if_omitted(self):
        oblg = self._create_obligee(omit=[u'zip'])
        self.assertEqual(oblg.zip, u'')

    def test_iczsj_field(self):
        neighbourhood = self._create_neighbourhood()
        oblg = self._create_obligee(iczsj=neighbourhood)
        self.assertEqual(oblg.iczsj, neighbourhood)

    def test_iczsj_field_may_not_be_omitted(self):
        with self.assertRaisesMessage(IntegrityError, u'NOT NULL constraint failed: obligees_obligee.iczsj'):
            self._create_obligee(omit=[u'iczsj'])

    def test_emails_field(self):
        oblg = self._create_obligee(emails=u'agency@example.com')
        self.assertEqual(oblg.emails, u'agency@example.com')

    def test_emails_field_default_value_if_omitted(self):
        oblg = self._create_obligee(omit=[u'emails'])
        self.assertEqual(oblg.emails, u'')

    def test_emails_field_validation_with_invalid_email(self):
        oblg = self._create_obligee(emails=u'invalid')
        with self.assertRaisesMessage(ValidationError, u'"invalid" is not a valid email address'):
            oblg.full_clean()

    def test_emails_field_validation_with_normalized_email(self):
        oblg = self._create_obligee(emails=u'"John" Smith <smith@example.com>')
        oblg.full_clean() # u'Parsed as: John Smith <smith@example.com>'

    def test_emails_field_validation_with_valid_email(self):
        oblg = self._create_obligee(emails=u'John Smith <smith@example.com>')
        oblg.full_clean()

    def test_latitude_field(self):
        oblg = self._create_obligee(latitude=44.11388888888889)
        self.assertEquals(oblg.latitude, 44.11388888888889)

    def test_latitude_field_default_value_if_omitted(self):
        oblg = self._create_obligee(omit=[u'latitude'])
        self.assertIsNone(oblg.latitude)

    def test_longitude_field(self):
        oblg = self._create_obligee(longitude=-85.03111111111112)
        self.assertEquals(oblg.longitude, -85.03111111111112)

    def test_longitude_field_default_value_if_omitted(self):
        oblg = self._create_obligee(omit=[u'longitude'])
        self.assertIsNone(oblg.longitude)

    def test_tags_relation(self):
        oblg = self._create_obligee()
        tag1 = self._create_obligee_tag(key=u'Key 1', name=u'Tag 1')
        tag2 = self._create_obligee_tag(key=u'Key 2', name=u'Tag 2')
        oblg.tags.add(tag1, tag2)
        self.assertItemsEqual(oblg.tags.all(), [tag1, tag2])

    def test_tags_relation_empty_by_default(self):
        oblg = self._create_obligee()
        self.assertItemsEqual(oblg.tags.all(), [])

    def test_groups_relation(self):
        oblg = self._create_obligee()
        group1 = self._create_obligee_group(key=u'Key 1', name=u'Group 1')
        group2 = self._create_obligee_group(key=u'Key 2', name=u'Group 2')
        oblg.groups.add(group1, group2)
        self.assertItemsEqual(oblg.groups.all(), [group1, group2])

    def test_groups_relation_empty_by_default(self):
        oblg = self._create_obligee()
        self.assertItemsEqual(oblg.groups.all(), [])

    def test_type_field(self):
        tests = (
                (Obligee.TYPES.SECTION_1, _(u'obligees:Obligee:type:SECTION_1')),
                (Obligee.TYPES.SECTION_2, _(u'obligees:Obligee:type:SECTION_2')),
                (Obligee.TYPES.SECTION_3, _(u'obligees:Obligee:type:SECTION_3')),
                (Obligee.TYPES.SECTION_4, _(u'obligees:Obligee:type:SECTION_4')),
                )
        # Make sure we are testing all defined obligee types
        tested_types = [a for a, __ in tests]
        defined_types = Obligee.TYPES._inverse.keys()
        self.assertItemsEqual(tested_types, defined_types)

        for type, expected_display  in tests:
            oblg = self._create_obligee(type=type)
            self.assertEqual(oblg.type, type)
            self.assertEqual(oblg.get_type_display(), expected_display)

    def test_type_field_may_not_be_omitted(self):
        with self.assertRaisesMessage(IntegrityError, u'NOT NULL constraint failed: obligees_obligee.type'):
            self._create_obligee(omit=[u'type'])

    def test_official_description_field(self):
        oblg = self._create_obligee(official_description=u'Agency\'s official description.')
        self.assertEqual(oblg.official_description, u'Agency\'s official description.')

    def test_official_description_field_default_value_if_omitted(self):
        oblg = self._create_obligee(omit=[u'official_description'])
        self.assertEqual(oblg.official_description, u'')

    def test_simple_description_field(self):
        oblg = self._create_obligee(simple_description=u'Agency\'s simple description.')
        self.assertEqual(oblg.simple_description, u'Agency\'s simple description.')

    def test_simple_description_field_default_value_if_omitted(self):
        oblg = self._create_obligee(omit=[u'simple_description'])
        self.assertEqual(oblg.simple_description, u'')

    def test_status_field(self):
        tests = (
                (Obligee.STATUSES.PENDING, _(u'obligees:Obligee:status:PENDING')),
                (Obligee.STATUSES.DISSOLVED, _(u'obligees:Obligee:status:DISSOLVED')),
                )
        # Make sure we are testing all defined obligee statuses
        tested_statuses = [a for a, __ in tests]
        defined_statuses = Obligee.STATUSES._inverse.keys()
        self.assertItemsEqual(tested_statuses, defined_statuses)

        for status, expected_display in tests:
            oblg = self._create_obligee(status=status)
            self.assertEqual(oblg.status, status)
            self.assertEqual(oblg.get_status_display(), expected_display)

    def test_status_field_may_not_be_omitted(self):
        with self.assertRaisesMessage(IntegrityError, u'NOT NULL constraint failed: obligees_obligee.status'):
            self._create_obligee(omit=[u'status'])

    def test_notes_field(self):
        oblg = self._create_obligee(notes=u'Notes about agency.')
        self.assertEqual(oblg.notes, u'Notes about agency.')

    def test_notes_field_default_value_if_omitted(self):
        oblg = self._create_obligee(omit=[u'notes'])
        self.assertEqual(oblg.notes, u'')

    def test_historical_obligee_model_exists(self):
        oblg = self._create_obligee(name=u'Agency', street=u'Westside')
        count = HistoricalObligee.objects.filter(id=oblg.pk).count()
        self.assertEqual(count, 1)

    def test_history_records_changes_to_official_name_field(self):
        oblg = self._create_obligee(official_name=u'Agency Official')
        oblg.official_name = u'Secret Agency Official'
        oblg.save()
        history = oblg.history.all()
        self.assertEqual([h.official_name for h in history], [u'Secret Agency Official', u'Agency Official'])

    def test_history_records_changes_to_name_field(self):
        oblg = self._create_obligee(name=u'Agency')
        oblg.name = u'Secret Agency'
        oblg.save()
        history = oblg.history.all()
        self.assertEqual([h.name for h in history], [u'Secret Agency', u'Agency'])

    def test_history_records_changes_to_slug_field_when_name_field_changes(self):
        oblg = self._create_obligee(name=u'Agency')
        oblg.name = u'Another Agency'
        oblg.save()
        history = oblg.history.all()
        self.assertEqual([h.slug for h in history], [u'another-agency', u'agency'])

    def test_history_records_changes_to_name_genitive_field(self):
        oblg = self._create_obligee(name_genitive=u'Agency genitive')
        oblg.name_genitive = u'Agency another genitive'
        oblg.save()
        history = oblg.history.all()
        self.assertEqual([h.name_genitive for h in history], [u'Agency another genitive', u'Agency genitive'])

    def test_history_records_changes_to_name_dative_field(self):
        oblg = self._create_obligee(name_dative=u'Agency dative')
        oblg.name_dative = u'Agency another dative'
        oblg.save()
        history = oblg.history.all()
        self.assertEqual([h.name_dative for h in history], [u'Agency another dative', u'Agency dative'])

    def test_history_records_changes_to_name_accusative_field(self):
        oblg =self._create_obligee(name_accusative=u'Agency accusative')
        oblg.name_accusative = u'Agency another accusative'
        oblg.save()
        history = oblg.history.all()
        self.assertEqual([h.name_accusative for h in history], [u'Agency another accusative', u'Agency accusative'])

    def test_history_records_changes_to_name_locative_field(self):
        oblg = self._create_obligee(name_locative=u'Agency locative')
        oblg.name_locative = u'Agency another locative'
        oblg.save()
        history = oblg.history.all()
        self.assertEqual([h.name_locative for h in history], [u'Agency another locative', u'Agency locative'])

    def test_history_records_changes_to_name_instrumental_field(self):
        oblg = self._create_obligee(name_instrumental=u'Agency instrumental')
        oblg.name_instrumental = u'Agency another instrumental'
        oblg.save()
        history = oblg.history.all()
        self.assertEqual([h.name_instrumental for h in history], [u'Agency another instrumental', u'Agency instrumental'])

    def test_history_records_changes_to_gender_field(self):
        oblg = self._create_obligee(gender=Obligee.GENDERS.MASCULINE)
        oblg.gender = Obligee.GENDERS.FEMININE
        oblg.save()
        history = oblg.history.all()
        self.assertEqual([h.gender for h in history], [Obligee.GENDERS.FEMININE, Obligee.GENDERS.MASCULINE])

    def test_history_records_changes_to_ico_field(self):
        oblg = self._create_obligee(ico=u'12345678')
        oblg.ico = u'87654321'
        oblg.save()
        history = oblg.history.all()
        self.assertEqual([h.ico for h in history], [u'87654321', u'12345678'])

    def test_history_records_changes_to_street_field(self):
        oblg = self._create_obligee(street=u'123 Westside')
        oblg.street = u'123 Eastside'
        oblg.save()
        history = oblg.history.all()
        self.assertEqual([h.street for h in history], [u'123 Eastside', u'123 Westside'])

    def test_history_records_changes_to_city_field(self):
        oblg = self._create_obligee(city=u'Winterfield')
        oblg.city = u'Springfield'
        oblg.save()
        history = oblg.history.all()
        self.assertEqual([h.city for h in history], [u'Springfield', u'Winterfield'])

    def test_history_records_changes_to_zip_field(self):
        oblg = self._create_obligee(zip=u'12345')
        oblg.zip = u'99999'
        oblg.save()
        history = oblg.history.all()
        self.assertEqual([h.zip for h in history], [u'99999', u'12345'])

    def test_history_records_changes_to_iczsj_field(self):
        neighbourhood1 = self._create_neighbourhood(id=u'12312')
        neighbourhood2 = self._create_neighbourhood(id=u'12345')
        oblg = self._create_obligee(iczsj=neighbourhood1)
        oblg.iczsj = neighbourhood2
        oblg.save()
        history = oblg.history.all()
        self.assertEqual([h.iczsj_id for h in history], [u'12345', u'12312'])

    def test_history_records_changes_to_emails_field(self):
        oblg = self._create_obligee(emails=u'agency@example.com')
        oblg.emails = u'agency@example.com, another@example.com'
        oblg.save()
        history = oblg.history.all()
        self.assertEqual([h.emails for h in history], [u'agency@example.com, another@example.com', u'agency@example.com'])

    def test_history_records_changes_to_latitude_field(self):
        oblg = self._create_obligee(latitude=44.11388888888889)
        oblg.latitude = -23.451
        oblg.save()
        history = oblg.history.all()
        self.assertEqual([h.latitude for h in history], [-23.451, 44.11388888888889])

    def test_history_records_changes_to_longitude_field(self):
        oblg = self._create_obligee(longitude=-85.03111111111112)
        oblg.longitude = 13.8321
        oblg.save()
        history = oblg.history.all()
        self.assertEqual([h.longitude for h in history], [13.8321, -85.03111111111112])

    def test_history_does_not_record_changes_to_tags_field(self):
        oblg = self._create_obligee()
        tag1 = self._create_obligee_tag(key=u'Key 1', name=u'Tag 1')
        tag2 = self._create_obligee_tag(key=u'Key 2', name=u'Tag 2')
        oblg.tags.add(tag1)
        oblg.tags.add(tag2)
        history = oblg.history.all()
        self.assertEqual(history.count(), 1)
        with self.assertRaisesMessage(AttributeError, u"'HistoricalObligee' object has no attribute 'tags'"):
            history[0].tags


    def test_history_does_not_record_changes_to_groups_field(self):
        oblg = self._create_obligee()
        group1 = self._create_obligee_group(key=u'Key 1', name=u'Group 1')
        group2 = self._create_obligee_group(key=u'Key 2', name=u'Group 2')
        oblg.groups.add(group1)
        oblg.groups.add(group2)
        history = oblg.history.all()
        self.assertEqual(history.count(), 1)
        with self.assertRaisesMessage(AttributeError, u"'HistoricalObligee' object has no attribute 'groups'"):
            history[0].groups

    def test_history_records_changes_to_type_field(self):
        oblg = self._create_obligee(type=Obligee.TYPES.SECTION_1)
        oblg.type = Obligee.TYPES.SECTION_2
        oblg.save()
        history = oblg.history.all()
        self.assertEqual([h.type for h in history], [Obligee.TYPES.SECTION_2, Obligee.TYPES.SECTION_1])

    def history_records_changes_to_official_description_field(self):
        oblg = self._create_obligee(official_description=u'Agency\'s official description.')
        oblg.official_description = u'Agency\'s another official description.'
        oblg.save()
        history = oblg.history.all()
        self.assertEqual([h.official_description for h in history], [u'Agency\'s another official description.', u'Agency\'s official description.'])

    def history_records_changes_to_simple_description_field(self):
        oblg = self._create_obligee(simple_description=u'Agency\'s simple description.')
        oblg.simple_description = u'Agency\'s another simple description.'
        oblg.save()
        history = oblg.history.all()
        self.assertEqual([h.simple_description for h in history], [u'Agency\'s another simple description.', u'Agency\'s simple description.'])

    def test_history_records_changes_to_status_field(self):
        oblg = self._create_obligee(status=Obligee.STATUSES.PENDING)
        oblg.status = Obligee.STATUSES.DISSOLVED
        oblg.save()
        history = oblg.history.all()
        self.assertEqual([h.status for h in history], [Obligee.STATUSES.DISSOLVED, Obligee.STATUSES.PENDING])

    def test_history_records_changes_to_notes_field(self):
        oblg = self._create_obligee(notes=u'Notes about agency.')
        oblg.notes = u'Some other notes about agency.'
        oblg.save()
        history = oblg.history.all()
        self.assertEqual([h.notes for h in history], [u'Some other notes about agency.', u'Notes about agency.'])

    def test_history_records_multiple_changes(self):
        oblg = self._create_obligee(name=u'Agency', street=u'Westside', status=Obligee.STATUSES.PENDING)
        oblg.name = u'Secret Agency'
        oblg.save()
        oblg.street = u'Eastside'
        oblg.save()
        oblg.status = Obligee.STATUSES.DISSOLVED
        oblg.save()

        history = oblg.history.all()
        expected_history = [
                (u'Secret Agency', u'Eastside', u'secret-agency', Obligee.STATUSES.DISSOLVED),
                (u'Secret Agency', u'Eastside', u'secret-agency', Obligee.STATUSES.PENDING),
                (u'Secret Agency', u'Westside', u'secret-agency', Obligee.STATUSES.PENDING),
                (u'Agency', u'Westside', u'agency', Obligee.STATUSES.PENDING),
                ]
        self.assertEqual([(h.name, h.street, h.slug, h.status) for h in history], expected_history)

    def test_obligeealias_set_relation(self):
        oblg = self._create_obligee()
        alias = self._create_obligee_alias(obligee=oblg)
        self.assertItemsEqual(oblg.obligeealias_set.all(), [alias])

    def test_obligeealias_set_relation_empty_by_default(self):
        oblg = self._create_obligee()
        self.assertItemsEqual(oblg.obligeealias_set.all(), [])

    def test_branch_set_relation(self):
        oblg = self._create_obligee()
        branch = self._create_branch(obligee=oblg)
        self.assertItemsEqual(oblg.branch_set.all(), [branch])

    def test_branch_set_relation_empty_by_default(self):
        oblg = self._create_obligee()
        self.assertItemsEqual(oblg.branch_set.all(), [])

    def test_inforequestdraft_set_relation(self):
        oblg = self._create_obligee()
        draft = self._create_inforequest_draft(obligee=oblg)
        self.assertItemsEqual(oblg.inforequestdraft_set.all(), [draft])

    def test_inforequestdraft_set_relation_empty_by_default(self):
        oblg = self._create_obligee()
        self.assertItemsEqual(oblg.inforequestdraft_set.all(), [])

    def test_obligeetag_obligee_set_backward_relation(self):
        tag = self._create_obligee_tag()
        oblg1 = self._create_obligee()
        oblg2 = self._create_obligee()
        oblg1.tags.add(tag)
        oblg2.tags.add(tag)
        self.assertItemsEqual(tag.obligee_set.all(), [oblg1, oblg2])

    def test_obligeetag_obligee_set_backward_relation_empty_by_default(self):
        tag = self._create_obligee_tag()
        self.assertItemsEqual(tag.obligee_set.all(), [])

    def test_obligeegroup_obligee_set_backward_relation(self):
        group = self._create_obligee_group()
        oblg1 = self._create_obligee()
        oblg2 = self._create_obligee()
        oblg1.groups.add(group)
        oblg2.groups.add(group)
        self.assertItemsEqual(group.obligee_set.all(), [oblg1, oblg2])

    def test_obligeegroup_obligee_set_backward_relation_empty_by_default(self):
        group = self._create_obligee_group()
        self.assertItemsEqual(group.obligee_set.all(), [])

    def test_no_default_ordering(self):
        self.assertFalse(Obligee.objects.all().ordered)

    def test_dummy_email_property(self):
        oblg = self._create_obligee(name=u'Agency')
        self.assertEqual(oblg.dummy_email(oblg.name, u'{name}@chcemvediet.sk'), u'agency@chcemvediet.sk')

    def test_dummy_email_property_with_accent_in_name(self):
        name=u'ÍňŤéřńÁťǏônǎĺ AGENCY Москва'
        self.assertEqual(Obligee.dummy_email(name, u'{name}@chcemvediet.sk'), u'international-agency-moskva@chcemvediet.sk')

    def test_dummy_email_property_with_too_long_name(self):
        name = u'x' * 40
        self.assertEqual(Obligee.dummy_email(name, u'{name}@chcemvediet.sk'), u'x' * 30 + u'@chcemvediet.sk')

    def test_dummy_email_property_with_hyphens_in_name(self):
        name = u'--International Student--Agency--  '
        self.assertEqual(Obligee.dummy_email(name, u'{name}@chcemvediet.sk'), u'international-student-agency@chcemvediet.sk')

    def test_dummy_email_property_with_multiple_placeholders(self):
        name = u'Agency'
        self.assertEqual(Obligee.dummy_email(name, u'{name}-{name}@chcemvediet.sk'), u'agency-agency@chcemvediet.sk')

    def test_dummy_email_property_with_invalid_placeholder(self):
        with self.assertRaisesMessage(KeyError, u'invalid'):
            name = u'Agency'
            Obligee.dummy_email(name, u'{invalid}@chcemvediet.sk')

    def test_dummy_email_property_without_placeholder(self):
        name = u'Agency'
        self.assertEqual(Obligee.dummy_email(name, u'@chcemvediet.sk'), u'@chcemvediet.sk')

    def test_emails_parsed_property(self):
        oblg = self._create_obligee(emails=u'The Agency <agency@example.com>')
        self.assertEqual(list(oblg.emails_parsed), [(u'The Agency', u'agency@example.com')])

    def test_emails_parsed_property_with_comma_in_name(self):
        oblg = self._create_obligee(emails=u'"Agency, The" <agency@example.com>')
        self.assertEqual(list(oblg.emails_parsed), [(u'Agency, The', u'agency@example.com')])

    def test_emails_parsed_property_with_quotes_in_name(self):
        oblg = self._create_obligee(emails=u'"The \\"Secret\\" Agency" <agency@example.com>')
        self.assertEqual(list(oblg.emails_parsed), [(u'The "Secret" Agency', u'agency@example.com')])

    def test_emails_parsed_property_with_empty_name(self):
        oblg = self._create_obligee(emails=u'     <agency@example.com>')
        self.assertEqual(list(oblg.emails_parsed), [(u'', u'agency@example.com')])

    def test_emails_parsed_property_without_name(self):
        oblg = self._create_obligee(emails=u'agency@example.com')
        self.assertEqual(list(oblg.emails_parsed), [(u'', u'agency@example.com')])

    def test_emails_parsed_property_with_multiple_mails(self):
        oblg = self._create_obligee(emails=u'The Agency <agency@example.com>, Another Mail <another@example.com>')
        self.assertEqual(list(oblg.emails_parsed), [(u'The Agency', u'agency@example.com'), (u'Another Mail', u'another@example.com')])

    def test_emails_parsed_property_with_empty_mails(self):
        oblg = self._create_obligee(emails=u'  , The Agency <agency@example.com>,  ,   ')
        self.assertEqual(list(oblg.emails_parsed), [(u'The Agency', u'agency@example.com')])

    def test_emails_parsed_property_with_no_emails(self):
        oblg = self._create_obligee(emails=u'')
        self.assertEqual(list(oblg.emails_parsed), [])

    def test_emails_formatted_property(self):
        oblg = self._create_obligee(emails=u'The Agency <agency@example.com>')
        self.assertEqual(list(oblg.emails_formatted), [u'The Agency <agency@example.com>'])

    def test_emails_formatted_property_with_comma_in_name(self):
        oblg = self._create_obligee(emails=u'"Agency, The" <agency@example.com>')
        self.assertEqual(list(oblg.emails_formatted), [u'"Agency, The" <agency@example.com>'])

    def test_emails_formatted_property_with_quotes_in_name(self):
        oblg = self._create_obligee(emails=u'"The \\"Secret\\" Agency" <agency@example.com>')
        self.assertEqual(list(oblg.emails_formatted), [u'"The \\"Secret\\" Agency" <agency@example.com>'])

    def test_emails_formatted_property_with_empty_name(self):
        oblg = self._create_obligee(emails=u'     <agency@example.com>')
        self.assertEqual(list(oblg.emails_formatted), [u'agency@example.com'])

    def test_emails_formatted_property_without_name(self):
        oblg = self._create_obligee(emails=u'agency@example.com')
        self.assertEqual(list(oblg.emails_formatted), [u'agency@example.com'])

    def test_emails_formatted_property_with_multiple_mails(self):
        oblg = self._create_obligee(emails=u'The Agency <agency@example.com>, Another Mail <another@example.com>')
        self.assertEqual(list(oblg.emails_formatted), [u'The Agency <agency@example.com>', u'Another Mail <another@example.com>'])

    def test_emails_formatted_property_with_empty_mails(self):
        oblg = self._create_obligee(emails=u'  , The Agency <agency@example.com>,  ,   ')
        self.assertEqual(list(oblg.emails_formatted), [u'The Agency <agency@example.com>'])

    def test_emails_formatted_property_with_no_emails(self):
        oblg = self._create_obligee(emails=u'')
        self.assertEqual(list(oblg.emails_formatted), [])

    def test_repr(self):
        oblg = self._create_obligee(name=u'Agency')
        self.assertEqual(repr(oblg), u'<Obligee: [{}] Agency>'.format(oblg.pk))

    def test_pending_query_method(self):
        oblg1 = self._create_obligee(name=u'Agency 1', status=Obligee.STATUSES.DISSOLVED)
        oblg2 = self._create_obligee(name=u'Agency 2', status=Obligee.STATUSES.DISSOLVED)
        oblg3 = self._create_obligee(name=u'Agency 3', status=Obligee.STATUSES.PENDING)
        oblg4 = self._create_obligee(name=u'Agency 4', status=Obligee.STATUSES.PENDING)
        self.assertItemsEqual(Obligee.objects.filter(name__startswith=u'Agency').pending(), [oblg3, oblg4])

    def test_order_by_pk_query_method(self):
        oblgs = [self._create_obligee() for __ in range(20)]
        sample = random.sample(oblgs, 10)
        result = Obligee.objects.filter(pk__in=(d.pk for d in sample)).order_by_pk().reverse()
        self.assertEqual(list(result), sorted(sample, key=lambda d: -d.pk))

    def test_order_by_name_query_method(self):
        names = [u'aaa', u'bbb', u'ccc', u'ddd', u'eee', u'fff', u'ggg', u'hhh', u'iii', u'jjj']
        random.shuffle(names)
        oblgs = [self._create_obligee(name=n) for n in names]
        self.assertEqual(list(Obligee.objects.filter(name__in=names).order_by_name()), sorted(oblgs, key=lambda o: o.name))
