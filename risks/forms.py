from django import forms

from accounts.models import User
from core.forms import TenantModelForm
from tenancy.models import Membership

from .models import Risk


class RiskForm(TenantModelForm):
    class Meta:
        model = Risk
        fields = [
            "title", "description", "category", "asset_process", "threat", "vulnerability",
            "likelihood", "impact", "existing_controls",
            "residual_likelihood", "residual_impact",
            "owner", "treatment", "treatment_owner", "treatment_plan", "due_date", "status",
            "related_requirements",
        ]
        widgets = {
            "title": forms.TextInput(attrs={"class": "form-input"}),
            "description": forms.Textarea(attrs={"class": "form-textarea", "rows": 3}),
            "category": forms.Select(attrs={"class": "form-select"}),
            "asset_process": forms.TextInput(attrs={"class": "form-input"}),
            "threat": forms.TextInput(attrs={"class": "form-input"}),
            "vulnerability": forms.TextInput(attrs={"class": "form-input"}),
            "likelihood": forms.Select(attrs={"class": "form-select"}),
            "impact": forms.Select(attrs={"class": "form-select"}),
            "existing_controls": forms.Textarea(attrs={"class": "form-textarea", "rows": 2}),
            "residual_likelihood": forms.Select(attrs={"class": "form-select"}),
            "residual_impact": forms.Select(attrs={"class": "form-select"}),
            "owner": forms.Select(attrs={"class": "form-select"}),
            "treatment": forms.Select(attrs={"class": "form-select"}),
            "treatment_owner": forms.Select(attrs={"class": "form-select"}),
            "treatment_plan": forms.Textarea(attrs={"class": "form-textarea", "rows": 2}),
            "due_date": forms.DateInput(attrs={"class": "form-input", "type": "date"}),
            "status": forms.Select(attrs={"class": "form-select"}),
            "related_requirements": forms.SelectMultiple(attrs={"class": "form-select"}),
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        if self.organisation is not None:
            from django.db.models import Q

            member_qs = User.objects.filter(
                id__in=Membership.objects.filter(organisation=self.organisation, is_active=True).values("user_id")
            )
            self.fields["owner"].queryset = member_qs
            self.fields["treatment_owner"].queryset = member_qs
            self.fields["related_requirements"].queryset = self.fields["related_requirements"].queryset.filter(
                Q(framework__organisation__isnull=True) | Q(framework__organisation=self.organisation)
            )
