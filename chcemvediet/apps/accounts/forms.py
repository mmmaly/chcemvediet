# vim: expandtab
from django import forms

class SignupForm(forms.Form):
    first_name = forms.CharField(
            max_length=30,
            label='First name',
            widget=forms.TextInput(attrs={'placeholder': 'First name'}),
            )
    last_name = forms.CharField(
            max_length=30,
            label='Last name',
            widget=forms.TextInput(attrs={'placeholder': 'Last name'}),
            )
    street = forms.CharField(
            max_length=100,
            label='Street',
            widget=forms.TextInput(attrs={'placeholder': 'Street'}),
            )
    city = forms.CharField(
            max_length=30,
            label='City',
            widget=forms.TextInput(attrs={'placeholder': 'City'}),
            )
    zip = forms.RegexField(
            max_length=5,
            label='Zip',
            widget=forms.TextInput(attrs={'placeholder': 'Zip'}),
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

