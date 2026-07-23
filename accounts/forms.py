from django import forms
from django.contrib.auth.forms import AuthenticationForm

from .models import User


class EmailAuthenticationForm(AuthenticationForm):
    username = forms.EmailField(
        label="Email address",
        widget=forms.EmailInput(attrs={"class": "form-input", "autofocus": True}),
    )
    password = forms.CharField(
        label="Password",
        widget=forms.PasswordInput(attrs={"class": "form-input"}),
    )


class ProfileForm(forms.ModelForm):
    class Meta:
        model = User
        fields = ["first_name", "last_name", "job_title", "phone_number"]
        widgets = {
            "first_name": forms.TextInput(attrs={"class": "form-input"}),
            "last_name": forms.TextInput(attrs={"class": "form-input"}),
            "job_title": forms.TextInput(attrs={"class": "form-input"}),
            "phone_number": forms.TextInput(attrs={"class": "form-input"}),
        }
