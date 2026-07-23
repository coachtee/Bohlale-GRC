from django import forms

from .models import FrameworkImport, REQUIREMENT_STATUS_CHOICES


class FrameworkImportForm(forms.ModelForm):
    class Meta:
        model = FrameworkImport
        fields = ["proposed_name", "source_file", "source_text"]
        widgets = {
            "proposed_name": forms.TextInput(attrs={"class": "form-input", "placeholder": "e.g. Client Supplier Code of Conduct"}),
            "source_file": forms.ClearableFileInput(attrs={"class": "form-input"}),
            "source_text": forms.Textarea(attrs={"class": "form-textarea", "rows": 10, "placeholder": "Paste the framework text here (used if no file is uploaded, or if the file type can't be parsed automatically)."}),
        }


class RequirementStatusForm(forms.Form):
    status = forms.ChoiceField(choices=REQUIREMENT_STATUS_CHOICES, widget=forms.Select(attrs={"class": "form-select"}))
    notes = forms.CharField(required=False, widget=forms.Textarea(attrs={"class": "form-textarea", "rows": 2}))


class ExtractedDataEditForm(forms.Form):
    extracted_json = forms.CharField(widget=forms.Textarea(attrs={"class": "form-textarea", "rows": 20}))
