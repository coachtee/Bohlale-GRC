from django import forms

from accounts.models import User
from core.forms import TenantModelForm
from tenancy.models import Membership

from .models import Control, IMPLEMENTATION_STATUS_CHOICES


class ControlForm(TenantModelForm):
    class Meta:
        model = Control
        fields = [
            "name", "description", "owner", "implementation_status", "effectiveness",
            "implementation_notes", "framework_requirements", "risks", "policies",
        ]
        widgets = {
            "name": forms.TextInput(attrs={"class": "form-input"}),
            "description": forms.Textarea(attrs={"class": "form-textarea", "rows": 3}),
            "owner": forms.Select(attrs={"class": "form-select"}),
            "implementation_status": forms.Select(attrs={"class": "form-select"}),
            "effectiveness": forms.Select(attrs={"class": "form-select"}),
            "implementation_notes": forms.Textarea(attrs={"class": "form-textarea", "rows": 3}),
            "framework_requirements": forms.SelectMultiple(attrs={"class": "form-select"}),
            "risks": forms.SelectMultiple(attrs={"class": "form-select"}),
            "policies": forms.SelectMultiple(attrs={"class": "form-select"}),
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        if self.organisation is not None:
            from django.db.models import Q

            self.fields["owner"].queryset = User.objects.filter(
                id__in=Membership.objects.filter(organisation=self.organisation, is_active=True).values("user_id")
            )
            self.fields["risks"].queryset = self.fields["risks"].queryset.filter(organisation=self.organisation)
            self.fields["policies"].queryset = self.fields["policies"].queryset.filter(organisation=self.organisation)
            self.fields["framework_requirements"].queryset = self.fields["framework_requirements"].queryset.filter(
                Q(framework__organisation__isnull=True) | Q(framework__organisation=self.organisation)
            )


class SoAEntryForm(forms.Form):
    applicable = forms.BooleanField(required=False)
    justification = forms.CharField(required=False, widget=forms.Textarea(attrs={"class": "form-textarea", "rows": 2}))
    implementation_status = forms.ChoiceField(choices=IMPLEMENTATION_STATUS_CHOICES, widget=forms.Select(attrs={"class": "form-select"}))
