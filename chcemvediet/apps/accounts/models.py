# vim: expandtab
# -*- coding: utf-8 -*-
from django.db import models
from django.db.models import Q, Count, Case, When, IntegerField
from django.utils.functional import cached_property
from django.contrib.auth.models import User
from jsonfield import JSONField

from poleno.mail.models import Message
from poleno.utils.models import QuerySet, OriginalValuesMixin
from poleno.utils.misc import FormatMixin, squeeze
from chcemvediet.apps.anonymization.models import AttachmentAnonymization, AttachmentFinalization
from chcemvediet.apps.inforequests.models import InforequestEmail
from chcemvediet.apps.inforequests.constants import DEFAULT_DAYS_TO_PUBLISH_INFOREQUEST


class ProfileQuerySet(QuerySet):
    def select_undecided_emails_count(self):
        u"""
        Use to select ``Profile.undecided_emails_count``.
        """
        return self.annotate(undecided_emails_count=Count(Case(
                When(user__inforequest__inforequestemail__type=InforequestEmail.TYPES.UNDECIDED, then=1),
                output_field=IntegerField())))

class Profile(FormatMixin, OriginalValuesMixin, models.Model):
    user = models.OneToOneField(User, on_delete=models.CASCADE)
    street = models.CharField(max_length=255)
    city = models.CharField(max_length=255)
    zip = models.CharField(max_length=10)

    anonymize_inforequests = models.BooleanField(default=True,
            help_text=squeeze(u"""
                If true, published inforequests will be shown anonymized, otherwise in their
                original version.
                """))

    # May be NULL; Should NOT be empty
    custom_anonymized_strings = JSONField(null=True, blank=True, default=None,
            help_text=squeeze(u"""
                User defined strings for anonymization. JSON must be an array of strings. NULL for
                default anonymization.
                """))

    # May NOT be NULL
    days_to_publish_inforequest = models.IntegerField(default=DEFAULT_DAYS_TO_PUBLISH_INFOREQUEST,
            help_text=squeeze(u"""
                User defined number of days after which inforequest can be marked as published,
                after closing inforequest.
                """))


    # Backward relations added to other models:
    #
    #  -- User.profile
    #     Should NOT raise DoesNotExist

    # Indexes:
    #  -- user: OneToOneField

    objects = ProfileQuerySet.as_manager()

    tracked_fields = [u'custom_anonymized_strings']

    @property
    def undecided_emails_set(self):
        u"""
        Queryset of all undecided emails assigned to inforequests owned by the user.
        """
        return Message.objects.filter(
                inforequest__closed=False,
                inforequest__applicant_id=self.user_id,
                inforequestemail__type=InforequestEmail.TYPES.UNDECIDED,
                )

    @cached_property
    def undecided_emails(self):
        u"""
        Cached list of all undecided emails assigned to inforequests owned by the user. The emails
        are ordered by ``processed``.
        """
        return list(self.undecided_emails_set.order_by_processed())

    @cached_property
    def undecided_emails_count(self):
        u"""
        Cached number of undecided emails assigned to inforequests owned by the user. May be
        prefetched with ``select_undecided_emails_count()`` queryset method, Takes advantage of
        ``Profile.undecided_emails`` if it is already fetched.
        """
        if u'undecided_emails' in self.__dict__:
            return len(self.undecided_emails)
        else:
            return self.undecided_emails_set.count()

    @cached_property
    def has_undecided_emails(self):
        u"""
        Cached flag if the user has any undecided emails assigned to his inforequests. Takes
        advantage of ``Profile.undecided_emails_count`` or ``Profile.undecided_emails`` if either
        is already fetched.
        """
        if u'undecided_emails_count' in self.__dict__:
            return bool(self.undecided_emails_count)
        elif u'undecided_emails' in self.__dict__:
            return bool(self.undecided_emails)
        else:
            return self.undecided_emails_set.exists()

    def save(self, *args, **kwargs):
        self._delete_outdated_attachments()
        super(Profile, self).save(*args, **kwargs)

    def _delete_outdated_attachments(self):
        if self._custom_anonymized_strings_changed():
            AttachmentFinalization.objects.owned_by(self.user).delete()
            AttachmentAnonymization.objects.owned_by(self.user).delete()

    def _custom_anonymized_strings_changed(self):
        old_custom_anonymized_strings = self.get_original_value(u'custom_anonymized_strings')
        new_custom_anonymized_strings = self.custom_anonymized_strings
        old_custom_anonymization = old_custom_anonymized_strings is not None
        new_custom_anonymization = new_custom_anonymized_strings is not None
        if not old_custom_anonymization and not new_custom_anonymization:
            return False
        if old_custom_anonymization != new_custom_anonymization:
            return True
        return set(old_custom_anonymized_strings) != set(new_custom_anonymized_strings)

    def __str__(self):
        return format(self.pk)
