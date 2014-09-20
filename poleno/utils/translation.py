# vim: expandtab
# -*- coding: utf-8 -*-
from django.utils.translation import get_language, activate

class translation(object):
    u"""
    Django management commands have disabled translations by default. You can call this function
    within a ``with`` statement to enable translations temporarily. After the ``with`` statement
    exists translation settings are reset back to their previous state. You cas use it anywhere
    else you need to ensure translations in a certain language.

    Example:
        # whatever language
        with translation('sk'):
            # 'sk' enabled
            pass
        # back to the original language
    """
    def __init__(self, language_code):
        self.language_code = language_code

    def __enter__(self):
        self.previous_code = get_language()
        activate(self.language_code)

    def __exit__(self, type, value, traceback):
        activate(self.previous_code)
