from django.conf import settings
from django.db import models

from core.models import ReferenceCodeMixin, TenantScopedModel

SEVERITY_CHOICES = [
    ("low", "Low"),
    ("medium", "Medium"),
    ("high", "High"),
    ("critical", "Critical"),
]

STATUS_CHOICES = [
    ("reported", "Reported"),
    ("investigating", "Investigating"),
    ("contained", "Contained"),
    ("resolved", "Resolved"),
    ("closed", "Closed"),
]


class Incident(ReferenceCodeMixin, TenantScopedModel):
    """Report an Incident (spec §25)."""

    REFERENCE_PREFIX = "INC"

    title = models.CharField(max_length=250)
    description = models.TextField(help_text="What happened?")
    occurred_at = models.DateTimeField(null=True, blank=True, help_text="When did it happen?")
    discovered_at = models.DateTimeField(null=True, blank=True, help_text="When was it discovered?")
    discovered_by = models.ForeignKey(
        settings.AUTH_USER_MODEL, on_delete=models.SET_NULL, null=True, blank=True, related_name="incidents_discovered"
    )
    systems_affected = models.TextField(blank=True)
    information_affected = models.TextField(blank=True)
    personal_info_involved = models.BooleanField(default=False)
    severity = models.CharField(max_length=20, choices=SEVERITY_CHOICES, default="medium")
    immediate_actions = models.TextField(blank=True)
    root_cause = models.TextField(blank=True)
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default="reported")
    closed_at = models.DateTimeField(null=True, blank=True)

    related_risks = models.ManyToManyField("risks.Risk", blank=True, related_name="incidents")
    related_controls = models.ManyToManyField("controls.Control", blank=True, related_name="incidents")

    class Meta:
        ordering = ["-created_at"]

    def __str__(self):
        return f"{self.reference_code} {self.title}"

    def save(self, *args, **kwargs):
        self.assign_reference_code()
        super().save(*args, **kwargs)


EVENT_TYPE_CHOICES = [
    ("new_employee", "New Employee"),
    ("employee_departure", "Employee Departure"),
    ("new_supplier", "New Supplier"),
    ("new_system", "New System"),
    ("new_office", "New Office"),
    ("new_business_process", "New Business Process"),
    ("policy_change", "Policy Change"),
    ("security_incident", "Security Incident"),
    ("data_breach", "Data Breach"),
    ("regulatory_change", "Regulatory Change"),
]

EVENT_STATUS_CHOICES = [
    ("open", "Open"),
    ("reviewed", "Reviewed"),
    ("closed", "Closed"),
]

# Which registers to suggest reviewing for each type of organisational
# change (spec §26 example: "A new cloud supplier has been added.
# Consider reviewing: Supplier Register, Risk Register, ..."). Values
# are (label, url_name) — url_name resolved via core.templatetags.nav
# safe_url so this degrades gracefully if a target app isn't reachable.
EVENT_TYPE_SUGGESTIONS = {
    "new_employee": [("Training Register", "registers:hub"), ("Access Control", "controls:list")],
    "employee_departure": [("Access Control", "controls:list"), ("Asset Register", "assets:list")],
    "new_supplier": [("Supplier Register", "suppliers:list"), ("Risk Register", "risks:list"), ("Asset Register", "assets:list")],
    "new_system": [("Asset Register", "assets:list"), ("Risk Register", "risks:list"), ("Controls", "controls:list")],
    "new_office": [("Asset Register", "assets:list"), ("Risk Register", "risks:list")],
    "new_business_process": [("Risk Register", "risks:list"), ("Knowledge Profile", "knowledge:profile")],
    "policy_change": [("Documents", "documents:list")],
    "security_incident": [("Incidents", "incidents:list"), ("Risk Register", "risks:list")],
    "data_breach": [("Incidents", "incidents:list"), ("Registers", "registers:hub")],
    "regulatory_change": [("Frameworks", "frameworks:list"), ("Documents", "documents:list")],
}


class ChangeEvent(TenantScopedModel):
    """Organisational Change Event (spec §26)."""

    event_type = models.CharField(max_length=30, choices=EVENT_TYPE_CHOICES)
    description = models.TextField(blank=True)
    reported_by = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.SET_NULL, null=True)
    status = models.CharField(max_length=20, choices=EVENT_STATUS_CHOICES, default="open")
    review_notes = models.TextField(blank=True)

    class Meta:
        ordering = ["-created_at"]

    def __str__(self):
        return f"{self.get_event_type_display()} — {self.created_at:%Y-%m-%d}"

    @property
    def suggestions(self):
        return EVENT_TYPE_SUGGESTIONS.get(self.event_type, [])
