# vim: expandtab
# -*- coding: utf-8 -*-
from django.core.urlresolvers import reverse
from django.conf import settings
from django.utils.translation import ugettext_lazy as _
from django.utils.http import urlencode
from django.utils.html import format_html

from admin_tools.menu import items, Menu
from admin_tools.dashboard import modules, Dashboard, AppIndexDashboard

from poleno.mail.models import Message
from chcemvediet.apps.inforequests.models import InforequestEmail

ADMIN_LINKS = [
        dict(
            title=_(u'List of unassigned received e-mails.'),
            viewname=u'admin:mail_message_changelist',
            urlargs=dict(type__exact=Message.TYPES.INBOUND, assigned=0),
            queryset=Message.objects.inbound().filter(inforequest__isnull=True),
            ),
        dict(
            title=_(u'List of undecided e-mails assigned to closed inforequests.'),
            viewname=u'admin:inforequests_inforequestemail_changelist',
            urlargs=dict(type__exact=InforequestEmail.TYPES.UNDECIDED, inforequest__closed__exact=1),
            queryset=InforequestEmail.objects.filter(type=InforequestEmail.TYPES.UNDECIDED, inforequest__closed=True),
            ),
        dict(
            title=_(u'List of e-mails marked as unrelated.'),
            viewname=u'admin:inforequests_inforequestemail_changelist',
            urlargs=dict(type__exact=InforequestEmail.TYPES.UNRELATED),
            queryset=InforequestEmail.objects.filter(type=InforequestEmail.TYPES.UNRELATED),
            ),
        dict(
            title=_(u"List of e-mails the user didn't know how to decide."),
            viewname=u'admin:inforequests_inforequestemail_changelist',
            urlargs=dict(type__exact=InforequestEmail.TYPES.UNKNOWN),
            queryset=InforequestEmail.objects.filter(type=InforequestEmail.TYPES.UNKNOWN),
            ),
        ]

if settings.DEBUG:
    ADMIN_LINKS += [
            dict(
                title=_(u'Timewarp'),
                viewname=u'admin:timewarp',
                ),
            ]

ADMIN_MODEL_GROUPS = [
        # Obligee models
        dict(
            title=_(u'Obligees'),
            models=[
                u'chcemvediet.apps.obligees.models.Obligee',
                u'chcemvediet.apps.obligees.models.HistoricalObligee',
                ],
            ),
        # Inforequest models
        dict(
            title=_(u'Inforequests'),
            models=[
                u'chcemvediet.apps.inforequests.models.InforequestDraft',
                u'chcemvediet.apps.inforequests.models.Inforequest',
                u'chcemvediet.apps.inforequests.models.InforequestEmail',
                u'chcemvediet.apps.inforequests.models.Branch',
                u'chcemvediet.apps.inforequests.models.Action',
                u'chcemvediet.apps.inforequests.models.ActionDraft',
                ],
            ),
        # E-mail and attachment models
        dict(
            title=_(u'E-mails'),
            models=[
                u'poleno.mail.*',
                u'poleno.attachments.*',
                ],
            ),
        # User, account and social account models
        dict(
            title=_(u'Accounts'),
            children=[
                dict(
                    title=_(u'Users'),
                    models=[
                        u'django.contrib.auth.*',
                        u'chcemvediet.apps.accounts.*',
                        ],
                    ),
                dict(
                    title=_(u'E-mail Addresses'),
                    models=[
                        u'allauth.account.*',
                        ],
                    ),
                dict(
                    title=_(u'Social Accounts'),
                    models=[
                        u'allauth.socialaccount.*',
                        ],
                    ),
                ],
            ),
        ]

class CustomMenu(Menu):

    def _create_model_group(self, title, models=None, children=None):
        assert models is None or children is None

        if children is not None:
            return items.MenuItem(title, children=[self._create_model_group(**c) for c in children])
        else:
            return items.ModelList(title, models=models)

    def _used_models(self, parent=None):
        res = []
        if parent is None:
            parent = self
        for child in parent.children:
            try:
                res.extend(list(child.models))
            except AttributeError:
                pass
            res.extend(self._used_models(child))
        return res

    def _create_link(self, title, viewname, urlargs=None, queryset=None):
        count = queryset.count() if queryset is not None else 0
        title = format_html(u'<b>{0} ({1})</b>', title, count) if count else title
        url = u'%s?%s' % (reverse(viewname), urlencode(urlargs)) if urlargs else reverse(viewname)
        return items.MenuItem(title, url=url)

    def init_with_context(self, context):
        # Link to home and bookmarks
        self.children.append(items.MenuItem(_(u'Dashboard'), reverse(u'admin:index')))
        self.children.append(items.Bookmarks())

        # Links submenu
        self.children.append(items.MenuItem(_(u'Administration'), children=[self._create_link(**l) for l in ADMIN_LINKS]))

        # Models submenu
        self.children.append(items.MenuItem(_(u'Models'), children=[self._create_model_group(**g) for g in ADMIN_MODEL_GROUPS]))
        self.children[-1].children.append(items.AppList(_(u'Other Models'), exclude=self._used_models()))


class CustomIndexDashboard(Dashboard):

    def _create_model_group(self, title, models=None, children=None):
        assert models is None or children is None

        if children is not None:
            return modules.Group(title, display=u'stacked', children=[self._create_model_group(**c) for c in children])
        else:
            return modules.ModelList(title, models=models)

    def _create_link(self, title, viewname, urlargs=None, queryset=None):
        count = queryset.count() if queryset is not None else 0
        title = format_html(u'<b>{0} ({1})</b>', title, count) if count else title
        url = u'%s?%s' % (reverse(viewname), urlencode(urlargs)) if urlargs else reverse(viewname)
        return dict(title=title, url=url)

    def init_with_context(self, context):
        # Links module
        self.children.append(modules.LinkList(_(u'Administration'), children=[self._create_link(**l) for l in ADMIN_LINKS]))

        # Models module
        self.children.append(modules.Group(_(u'Models'), display=u'accordion', children=[self._create_model_group(**g) for g in ADMIN_MODEL_GROUPS]))

        # Recent actions module
        self.children.append(modules.RecentActions(_('Recent Actions'), limit=5))

class CustomAppIndexDashboard(AppIndexDashboard):
    title = ''

    def init_with_context(self, context):
        # Model list module
        self.children.append(modules.ModelList(self.app_title, self.models))

        # Recent actions module
        self.children.append(modules.RecentActions(_('Recent Actions'), limit=5,
            include_list=self.get_app_content_types()))
