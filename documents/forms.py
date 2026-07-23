from django import forms

from accounts.models import User
from core.forms import TenantModelForm
from tenancy.models import Membership

from .models import Document


class DocumentForm(TenantModelForm):
    class Meta:
        model = Document
        fields = [
            "title", "doc_type", "classification", "owner", "content",
            "next_review_date", "related_frameworks",
        ]
        widgets = {
            "title": forms.TextInput(attrs={"class": "form-input"}),
            "doc_type": forms.Select(attrs={"class": "form-select"}),
            "classification": forms.Select(attrs={"class": "form-select"}),
            "owner": forms.Select(attrs={"class": "form-select"}),
            "content": forms.Textarea(attrs={"class": "form-textarea", "rows": 16}),
            "next_review_date": forms.DateInput(attrs={"class": "form-input", "type": "date"}),
            "related_frameworks": forms.SelectMultiple(attrs={"class": "form-select"}),
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        if self.organisation is not None:
            self.fields["owner"].queryset = User.objects.filter(
                id__in=Membership.objects.filter(organisation=self.organisation, is_active=True).values("user_id")
            )


class DocumentContentForm(forms.Form):
    content = forms.CharField(widget=forms.Textarea(attrs={"class": "form-textarea", "rows": 18}))
    change_reason = forms.CharField(
        required=False, widget=forms.TextInput(attrs={"class": "form-input", "placeholder": "Why is this changing? (optional)"})
    )
