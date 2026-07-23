from django import forms

from .constants import ORGANISATION_TYPE_CHOICES, ROLE_CHOICES
from .models import Organisation, OrganisationInvite


class OrganisationForm(forms.ModelForm):
    class Meta:
        model = Organisation
        fields = [
            "name",
            "organisation_type",
            "industry",
            "registration_number",
            "country",
            "province",
            "website",
            "size",
            "logo",
        ]
        widgets = {
            "name": forms.TextInput(attrs={"class": "form-input", "placeholder": "e.g. Naleli Innovators Business School"}),
            "organisation_type": forms.Select(attrs={"class": "form-select"}),
            "industry": forms.TextInput(attrs={"class": "form-input"}),
            "registration_number": forms.TextInput(attrs={"class": "form-input"}),
            "country": forms.TextInput(attrs={"class": "form-input"}),
            "province": forms.TextInput(attrs={"class": "form-input"}),
            "website": forms.URLInput(attrs={"class": "form-input"}),
            "size": forms.Select(attrs={"class": "form-select"}),
        }


class InviteMemberForm(forms.ModelForm):
    class Meta:
        model = OrganisationInvite
        fields = ["email", "role"]
        widgets = {
            "email": forms.EmailInput(attrs={"class": "form-input", "placeholder": "name@example.com"}),
            "role": forms.Select(attrs={"class": "form-select"}),
        }


class MembershipRoleForm(forms.Form):
    role = forms.ChoiceField(choices=ROLE_CHOICES, widget=forms.Select(attrs={"class": "form-select"}))
