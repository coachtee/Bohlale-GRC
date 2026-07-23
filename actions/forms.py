from django import forms

from accounts.models import User
from core.forms import TenantModelForm
from tenancy.models import Membership

from .models import CorrectiveAction


class CorrectiveActionForm(TenantModelForm):
    class Meta:
        model = CorrectiveAction
        fields = [
            "source", "finding_description", "severity", "root_cause", "action_description",
            "owner", "due_date", "status", "verification_notes",
        ]
        widgets = {
            "source": forms.Select(attrs={"class": "form-select"}),
            "finding_description": forms.Textarea(attrs={"class": "form-textarea", "rows": 3}),
            "severity": forms.Select(attrs={"class": "form-select"}),
            "root_cause": forms.Textarea(attrs={"class": "form-textarea", "rows": 2}),
            "action_description": forms.Textarea(attrs={"class": "form-textarea", "rows": 2}),
            "owner": forms.Select(attrs={"class": "form-select"}),
            "due_date": forms.DateInput(attrs={"class": "form-input", "type": "date"}),
            "status": forms.Select(attrs={"class": "form-select"}),
            "verification_notes": forms.Textarea(attrs={"class": "form-textarea", "rows": 2}),
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        if self.organisation is not None:
            self.fields["owner"].queryset = User.objects.filter(
                id__in=Membership.objects.filter(organisation=self.organisation, is_active=True).values("user_id")
            )
