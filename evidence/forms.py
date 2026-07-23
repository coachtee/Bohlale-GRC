from django import forms

from accounts.models import User
from core.forms import TenantModelForm
from tenancy.models import Membership

from .models import Evidence


class EvidenceForm(TenantModelForm):
    class Meta:
        model = Evidence
        fields = [
            "name", "evidence_type", "owner", "file", "notes",
            "validity_period_months", "expiry_date", "verification_status",
            "related_controls", "related_requirements", "related_risks",
        ]
        widgets = {
            "name": forms.TextInput(attrs={"class": "form-input"}),
            "evidence_type": forms.Select(attrs={"class": "form-select"}),
            "owner": forms.Select(attrs={"class": "form-select"}),
            "file": forms.ClearableFileInput(attrs={"class": "form-input"}),
            "notes": forms.Textarea(attrs={"class": "form-textarea", "rows": 3}),
            "validity_period_months": forms.NumberInput(attrs={"class": "form-input"}),
            "expiry_date": forms.DateInput(attrs={"class": "form-input", "type": "date"}),
            "verification_status": forms.Select(attrs={"class": "form-select"}),
            "related_controls": forms.SelectMultiple(attrs={"class": "form-select"}),
            "related_requirements": forms.SelectMultiple(attrs={"class": "form-select"}),
            "related_risks": forms.SelectMultiple(attrs={"class": "form-select"}),
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        if self.organisation is not None:
            self.fields["owner"].queryset = User.objects.filter(
                id__in=Membership.objects.filter(organisation=self.organisation, is_active=True).values("user_id")
            )
            self.fields["related_controls"].queryset = self.fields["related_controls"].queryset.filter(organisation=self.organisation)
            self.fields["related_risks"].queryset = self.fields["related_risks"].queryset.filter(organisation=self.organisation)
