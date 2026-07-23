from django.conf import settings
from django.db import models

from core.models import ReferenceCodeMixin, TenantScopedModel

AUDIT_TYPE_CHOICES = [
    ("internal", "Internal Audit"),
    ("external", "External Audit"),
    ("readiness", "Readiness Review"),
    ("supplier", "Supplier Audit"),
]

AUDIT_STATUS_CHOICES = [
    ("planned", "Planned"),
    ("in_progress", "In Progress"),
    ("findings_recorded", "Findings Recorded"),
    ("closed", "Closed"),
]

FINDING_SEVERITY_CHOICES = [
    ("observation", "Observation"),
    ("minor_nonconformity", "Minor Nonconformity"),
    ("major_nonconformity", "Major Nonconformity"),
]

FINDING_STATUS_CHOICES = [
    ("open", "Open"),
    ("in_progress", "In Progress"),
    ("closed", "Closed"),
]


class Audit(ReferenceCodeMixin, TenantScopedModel):
    """Audit lifecycle (spec §30): Plan -> Scope -> Schedule -> Assign
    Auditor -> Conduct -> Record Evidence -> Record Findings ->
    Corrective Actions -> Close. Scope/schedule/auditor are data fields
    on this record; status tracks the coarser conduct/closure stages."""

    REFERENCE_PREFIX = "AUD"

    title = models.CharField(max_length=250)
    audit_type = models.CharField(max_length=20, choices=AUDIT_TYPE_CHOICES, default="internal")
    framework = models.ForeignKey(
        "frameworks.Framework", on_delete=models.SET_NULL, null=True, blank=True, related_name="audits"
    )
    scope = models.TextField(blank=True)
    lead_auditor = models.ForeignKey(
        settings.AUTH_USER_MODEL, on_delete=models.SET_NULL, null=True, blank=True, related_name="audits_led"
    )
    scheduled_date = models.DateField(null=True, blank=True)
    start_date = models.DateField(null=True, blank=True)
    end_date = models.DateField(null=True, blank=True)
    status = models.CharField(max_length=20, choices=AUDIT_STATUS_CHOICES, default="planned")
    evidence = models.ManyToManyField("evidence.Evidence", blank=True, related_name="audits")
    closed_at = models.DateTimeField(null=True, blank=True)

    class Meta:
        ordering = ["-created_at"]

    def __str__(self):
        return f"{self.reference_code} {self.title}"

    def save(self, *args, **kwargs):
        self.assign_reference_code()
        super().save(*args, **kwargs)

    @property
    def open_major_findings_count(self):
        return self.findings.filter(severity="major_nonconformity").exclude(status="closed").count()


class AuditFinding(TenantScopedModel):
    audit = models.ForeignKey(Audit, on_delete=models.CASCADE, related_name="findings")
    requirement = models.ForeignKey(
        "frameworks.Requirement", on_delete=models.SET_NULL, null=True, blank=True, related_name="audit_findings"
    )
    control = models.ForeignKey(
        "controls.Control", on_delete=models.SET_NULL, null=True, blank=True, related_name="audit_findings"
    )
    description = models.TextField()
    severity = models.CharField(max_length=30, choices=FINDING_SEVERITY_CHOICES, default="observation")
    status = models.CharField(max_length=20, choices=FINDING_STATUS_CHOICES, default="open")
    evidence = models.ManyToManyField("evidence.Evidence", blank=True, related_name="audit_findings")

    class Meta:
        ordering = ["-created_at"]

    def __str__(self):
        return f"{self.audit} — {self.get_severity_display()}"
