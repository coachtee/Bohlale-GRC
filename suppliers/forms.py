from django import forms

from accounts.models import User
from core.forms import TenantModelForm
from tenancy.models import Membership

from .models import Supplier


class SupplierForm(TenantModelForm):
    class Meta:
        model = Supplier
        fields = [
            "name", "service", "owner", "criticality", "data_access", "personal_info_access",
            "risk_rating", "assessment_notes", "contract_review_date", "review_date", "status",
        ]
        widgets = {
            "name": forms.TextInput(attrs={"class": "form-input"}),
            "service": forms.TextInput(attrs={"class": "form-input"}),
            "owner": forms.Select(attrs={"class": "form-select"}),
            "criticality": forms.Select(attrs={"class": "form-select"}),
            "risk_rating": forms.Select(attrs={"class": "form-select"}),
            "assessment_notes": forms.Textarea(attrs={"class": "form-textarea", "rows": 3}),
            "contract_review_date": forms.DateInput(attrs={"class": "form-input", "type": "date"}),
            "review_date": forms.DateInput(attrs={"class": "form-input", "type": "date"}),
            "status": forms.Select(attrs={"class": "form-select"}),
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        if self.organisation is not None:
            self.fields["owner"].queryset = User.objects.filter(
                id__in=Membership.objects.filter(organisation=self.organisation, is_active=True).values("user_id")
            )
