from django import forms

from core.forms import TenantModelForm

from .models import ManagementReview


class ManagementReviewForm(TenantModelForm):
    class Meta:
        model = ManagementReview
        fields = ["framework", "meeting_date", "attendees", "agenda", "decisions", "attachment"]
        widgets = {
            "framework": forms.Select(attrs={"class": "form-select"}),
            "meeting_date": forms.DateInput(attrs={"class": "form-input", "type": "date"}),
            "attendees": forms.Textarea(attrs={"class": "form-textarea", "rows": 2}),
            "agenda": forms.Textarea(attrs={"class": "form-textarea", "rows": 3}),
            "decisions": forms.Textarea(attrs={"class": "form-textarea", "rows": 3}),
            "attachment": forms.ClearableFileInput(attrs={"class": "form-input"}),
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        if self.organisation is not None:
            from django.db.models import Q

            from frameworks.models import Framework

            self.fields["framework"].queryset = Framework.objects.filter(
                Q(organisation__isnull=True) | Q(organisation=self.organisation), is_published=True
            )
            self.fields["framework"].required = False


class InputRecordForm(forms.Form):
    covered = forms.BooleanField(required=False)
    notes = forms.CharField(required=False, widget=forms.Textarea(attrs={"class": "form-textarea", "rows": 2}))
