# vim: expandtab
# -*- coding: utf-8 -*-

from misc import Bunch

class FieldChoices(object):
    """
    Simple container for django model field choices following DRY principle.

    Example:
        class Mail(models.Model):
            STATUSES = FieldChoices(
                (UNKNOWN, 1, _(u'Unknown')),
                (DELIVERED, 2, _(u'Delivered')),
                (RETURNED, 3, _(u'Returned')),
                (LOST, 4, _(u'Lost')),
                )
            status = models.SmallIntegerField(choices=STATUSES._choices, verbose_name=_(u'Status'))

        mail = Mail()
        mail.status = mail.STATUSES.DELIVERED
    """

    def __init__(self, *args):
        choices = []
        for choice_name, choice_key, choice_value in args:
            if isinstance(choice_value, (list, tuple)): # It's a choice group
                group = []
                bunch = Bunch()
                for group_name, group_key, group_value in choice_value:
                    group.append((group_key, group_value))
                    bunch.__dict__[group_name] = group_key
                choices.append((choice_key, group))
                self.__dict__[choice_name] = bunch
            else:
                choices.append((choice_key, choice_value))
                self.__dict__[choice_name] = choice_key
        self._choices = choices

