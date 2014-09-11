# vim: expandtab
# -*- coding: utf-8 -*-
from django import forms

class WarpForm(forms.Form):
    jumpto = forms.DateTimeField(
            label=u'Jump To',
            required=False,
            input_formats=(
                u'%Y-%m-%d %H:%M:%S',
                u'%Y-%m-%d %H:%M',
                u'%Y-%m-%d',
                ),
            widget=forms.DateTimeInput(attrs={
                u'placeholder': u'yyyy-mm-dd hh:mm:ss',
                }),
            )
    speedup = forms.FloatField(
            label=u'Speedup',
            required=False,
            )
