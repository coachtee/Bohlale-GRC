from django import forms

from accounts.models import User
from core.forms import TenantModelForm
from tenancy.models import Membership

from .models import Asset


class AssetForm(TenantModelForm):
    class Meta:
        model = Asset
        fields = [
            "name", "asset_type", "owner", "classification", "location", "description",
            "related_process", "status", "related_risks", "related_controls", "related_suppliers",
        ]
        widgets = {
            "name": forms.TextInput(attrs={"class": "form-input"}),
            "asset_type": forms.Select(attrs={"class": "form-select"}),
            "owner": forms.Select(attrs={"class": "form-select"}),
            "classification": forms.Select(attrs={"class": "form-select"}),
            "location": forms.TextInput(attrs={"class": "form-input"}),
            "description": forms.Textarea(attrs={"class": "form-textarea", "rows": 3}),
            "related_process": forms.TextInput(attrs={"class": "form-input"}),
            "status": forms.Select(attrs={"class": "form-select"}),
            "related_risks": forms.SelectMultiple(attrs={"class": "form-select"}),
            "related_controls": forms.SelectMultiple(attrs={"class": "form-select"}),
            "related_suppliers": forms.SelectMultiple(attrs={"class": "form-select"}),
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        if self.organisation is not None:
            self.fields["owner"].queryset = User.objects.filter(
                id__in=Membership.objects.filter(organisation=self.organisation, is_active=True).values("user_id")
            )
            for field_name in ["related_risks", "related_controls", "related_suppliers"]:
                self.fields[field_name].queryset = self.fields[field_name].queryset.filter(organisation=self.organisation)
