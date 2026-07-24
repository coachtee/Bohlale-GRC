from django import forms

from .models import Framework, FrameworkImport, REQUIREMENT_STATUS_CHOICES


class FrameworkForm(forms.ModelForm):
    """Create a custom framework from scratch (Framework Library ->
    Create Framework Manually). Domains/requirements are added
    afterwards on the framework detail page via DomainQuickForm /
    RequirementQuickForm."""

    class Meta:
        model = Framework
        fields = ["name", "version", "description", "category"]
        widgets = {
            "name": forms.TextInput(attrs={"class": "form-input", "placeholder": "e.g. Client Supplier Code of Conduct"}),
            "version": forms.TextInput(attrs={"class": "form-input", "placeholder": "e.g. 2024 edition"}),
            "description": forms.Textarea(attrs={"class": "form-textarea", "rows": 3}),
            "category": forms.Select(attrs={"class": "form-select"}),
        }


class DomainQuickForm(forms.Form):
    title = forms.CharField(
        max_length=200, widget=forms.TextInput(attrs={"class": "form-input", "placeholder": "e.g. Access Management"})
    )
    code = forms.CharField(
        max_length=40, required=False,
        widget=forms.TextInput(attrs={"class": "form-input", "placeholder": "optional short code"}),
    )


class RequirementQuickForm(forms.Form):
    ref_code = forms.CharField(
        max_length=40, required=False,
        widget=forms.TextInput(attrs={"class": "form-input", "placeholder": "optional ref code"}),
    )
    title = forms.CharField(
        max_length=300, widget=forms.TextInput(attrs={"class": "form-input", "placeholder": "Requirement title"})
    )
    guidance = forms.CharField(
        required=False, widget=forms.Textarea(attrs={"class": "form-textarea", "rows": 2, "placeholder": "Plain-language guidance (optional)"})
    )


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
