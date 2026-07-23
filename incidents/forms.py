from django import forms

from core.forms import TenantModelForm

from .models import ChangeEvent, Incident


class IncidentForm(TenantModelForm):
    class Meta:
        model = Incident
        fields = [
            "title", "description", "occurred_at", "discovered_at", "systems_affected",
            "information_affected", "personal_info_involved", "severity", "immediate_actions", "status",
        ]
        widgets = {
            "title": forms.TextInput(attrs={"class": "form-input"}),
            "description": forms.Textarea(attrs={"class": "form-textarea", "rows": 4}),
            "occurred_at": forms.DateTimeInput(attrs={"class": "form-input", "type": "datetime-local"}),
            "discovered_at": forms.DateTimeInput(attrs={"class": "form-input", "type": "datetime-local"}),
            "systems_affected": forms.Textarea(attrs={"class": "form-textarea", "rows": 2}),
            "information_affected": forms.Textarea(attrs={"class": "form-textarea", "rows": 2}),
            "severity": forms.Select(attrs={"class": "form-select"}),
            "immediate_actions": forms.Textarea(attrs={"class": "form-textarea", "rows": 2}),
            "status": forms.Select(attrs={"class": "form-select"}),
        }


class ChangeEventForm(TenantModelForm):
    class Meta:
        model = ChangeEvent
        fields = ["event_type", "description"]
        widgets = {
            "event_type": forms.Select(attrs={"class": "form-select"}),
            "description": forms.Textarea(attrs={"class": "form-textarea", "rows": 3}),
        }
