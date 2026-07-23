from django import forms

from accounts.models import User
from core.forms import TenantModelForm
from tenancy.models import Membership

from .models import Audit, AuditFinding


class AuditForm(TenantModelForm):
    class Meta:
        model = Audit
        fields = ["title", "audit_type", "framework", "scope", "lead_auditor", "scheduled_date", "start_date", "end_date", "status"]
        widgets = {
            "title": forms.TextInput(attrs={"class": "form-input"}),
            "audit_type": forms.Select(attrs={"class": "form-select"}),
            "framework": forms.Select(attrs={"class": "form-select"}),
            "scope": forms.Textarea(attrs={"class": "form-textarea", "rows": 3}),
            "lead_auditor": forms.Select(attrs={"class": "form-select"}),
            "scheduled_date": forms.DateInput(attrs={"class": "form-input", "type": "date"}),
            "start_date": forms.DateInput(attrs={"class": "form-input", "type": "date"}),
            "end_date": forms.DateInput(attrs={"class": "form-input", "type": "date"}),
            "status": forms.Select(attrs={"class": "form-select"}),
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        if self.organisation is not None:
            from django.db.models import Q

            from frameworks.models import Framework

            self.fields["framework"].queryset = Framework.objects.filter(
                Q(organisation__isnull=True) | Q(organisation=self.organisation), is_published=True
            )
            self.fields["lead_auditor"].queryset = User.objects.filter(
                id__in=Membership.objects.filter(organisation=self.organisation, is_active=True).values("user_id")
            )


class AuditFindingForm(TenantModelForm):
    class Meta:
        model = AuditFinding
        fields = ["description", "severity", "status", "requirement", "control"]
        widgets = {
            "description": forms.Textarea(attrs={"class": "form-textarea", "rows": 3}),
            "severity": forms.Select(attrs={"class": "form-select"}),
            "status": forms.Select(attrs={"class": "form-select"}),
            "requirement": forms.Select(attrs={"class": "form-select"}),
            "control": forms.Select(attrs={"class": "form-select"}),
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        if self.organisation is not None:
            from django.db.models import Q

            self.fields["control"].queryset = self.fields["control"].queryset.filter(organisation=self.organisation)
            self.fields["requirement"].queryset = self.fields["requirement"].queryset.filter(
                Q(framework__organisation__isnull=True) | Q(framework__organisation=self.organisation)
            )
