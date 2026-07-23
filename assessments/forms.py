from django import forms

from core.forms import TenantModelForm
from frameworks.models import Framework

from .models import Assessment, AssessmentResult, RATING_CHOICES


class AssessmentCreateForm(TenantModelForm):
    class Meta:
        model = Assessment
        fields = ["name", "assessment_type", "framework", "assessor", "started_at"]
        widgets = {
            "name": forms.TextInput(attrs={"class": "form-input"}),
            "assessment_type": forms.Select(attrs={"class": "form-select"}),
            "framework": forms.Select(attrs={"class": "form-select"}),
            "assessor": forms.Select(attrs={"class": "form-select"}),
            "started_at": forms.DateInput(attrs={"class": "form-input", "type": "date"}),
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        if self.organisation is not None:
            from django.db.models import Q

            self.fields["framework"].queryset = Framework.objects.filter(
                Q(organisation__isnull=True) | Q(organisation=self.organisation), is_published=True
            )
            from accounts.models import User
            from tenancy.models import Membership

            self.fields["assessor"].queryset = User.objects.filter(
                id__in=Membership.objects.filter(organisation=self.organisation, is_active=True).values("user_id")
            )


class AssessmentResultForm(forms.ModelForm):
    class Meta:
        model = AssessmentResult
        fields = ["rating", "comments", "findings", "recommendations", "due_date"]
        widgets = {
            "rating": forms.Select(attrs={"class": "form-select"}),
            "comments": forms.Textarea(attrs={"class": "form-textarea", "rows": 2}),
            "findings": forms.Textarea(attrs={"class": "form-textarea", "rows": 2}),
            "recommendations": forms.Textarea(attrs={"class": "form-textarea", "rows": 2}),
            "due_date": forms.DateInput(attrs={"class": "form-input", "type": "date"}),
        }
