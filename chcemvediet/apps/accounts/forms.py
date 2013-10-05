# vim: expandtab
from django import forms
from django.utils.translation import ugettext_lazy as _

class SignupForm(forms.Form):
    first_name = forms.CharField(
            max_length=30,
            label=_(u'First name'),
            widget=forms.TextInput(attrs={'placeholder': _(u'First name')}),
            )
    last_name = forms.CharField(
            max_length=30,
            label=_(u'Last name'),
            widget=forms.TextInput(attrs={'placeholder': _(u'Last name')}),
            )
    street = forms.CharField(
            max_length=100,
            label=_(u'Street'),
            widget=forms.TextInput(attrs={'placeholder': _(u'Street')}),
            )
    city = forms.CharField(
            max_length=30,
            label=_(u'City'),
            widget=forms.TextInput(attrs={'placeholder': _(u'City')}),
            )
    zip = forms.RegexField(
            max_length=5,
            label=_(u'Zip'),
            widget=forms.TextInput(attrs={'placeholder': _(u'Zip')}),
            regex=r'^\d{5}$',
            )

    def save(self, user):
        user.first_name = self.cleaned_data['first_name']
        user.last_name = self.cleaned_data['last_name']
        user.save()
        user.profile.street = self.cleaned_data['street']
        user.profile.city = self.cleaned_data['city']
        user.profile.zip = self.cleaned_data['zip']
        user.profile.save()

