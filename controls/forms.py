from django import forms

from accounts.models import User
from core.forms import TenantModelForm
from tenancy.models import Membership

from .models import Control, IMPLEMENTATION_STATUS_CHOICES


class FrameworkRequirementMultipleChoiceField(forms.ModelMultipleChoiceField):
    """Labels each requirement with its framework code so a single
    multi-select can be used to map one control across many frameworks
    at once (spec: cross-framework control mapping) without the
    options becoming an unreadable flat list."""

    def label_from_instance(self, obj):
        return f"[{obj.framework.code}] {obj.ref_code} — {obj.title}"


class ControlForm(TenantModelForm):
    framework_requirements = FrameworkRequirementMultipleChoiceField(
        queryset=None, required=False, widget=forms.SelectMultiple(attrs={"class": "form-select", "size": 10}),
        help_text="Hold Ctrl/Cmd to select requirements from several frameworks — one control can map to many.",
    )

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
            "risks": forms.SelectMultiple(attrs={"class": "form-select"}),
            "policies": forms.SelectMultiple(attrs={"class": "form-select"}),
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        from django.db.models import Q

        from frameworks.models import Requirement

        base_qs = Requirement.objects.select_related("framework", "domain").order_by(
            "framework__name", "domain__order", "order"
        )
        if self.organisation is not None:
            self.fields["owner"].queryset = User.objects.filter(
                id__in=Membership.objects.filter(organisation=self.organisation, is_active=True).values("user_id")
            )
            self.fields["risks"].queryset = self.fields["risks"].queryset.filter(organisation=self.organisation)
            self.fields["policies"].queryset = self.fields["policies"].queryset.filter(organisation=self.organisation)
            base_qs = base_qs.filter(
                Q(framework__organisation__isnull=True) | Q(framework__organisation=self.organisation)
            )
        self.fields["framework_requirements"].queryset = base_qs


class SoAEntryForm(forms.Form):
    applicable = forms.BooleanField(required=False)
    justification = forms.CharField(required=False, widget=forms.Textarea(attrs={"class": "form-textarea", "rows": 2}))
    implementation_status = forms.ChoiceField(choices=IMPLEMENTATION_STATUS_CHOICES, widget=forms.Select(attrs={"class": "form-select"}))
