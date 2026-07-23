from django.conf import settings
from django.contrib.contenttypes.fields import GenericForeignKey
from django.contrib.contenttypes.models import ContentType
from django.db import models

from core.models import ReferenceCodeMixin, TenantScopedModel

SOURCE_CHOICES = [
    ("audit", "Audit"),
    ("assessment", "Assessment"),
    ("incident", "Incident"),
    ("risk_review", "Risk Review"),
    ("management_review", "Management Review"),
    ("other", "Other"),
]

SEVERITY_CHOICES = [
    ("low", "Low"),
    ("medium", "Medium"),
    ("high", "High"),
]

STATUS_OPEN = "open"
STATUS_IN_PROGRESS = "in_progress"
STATUS_VERIFICATION = "verification"
STATUS_CLOSED = "closed"

STATUS_CHOICES = [
    (STATUS_OPEN, "Open"),
    (STATUS_IN_PROGRESS, "In Progress"),
    (STATUS_VERIFICATION, "Pending Verification"),
    (STATUS_CLOSED, "Closed"),
]


class CorrectiveAction(ReferenceCodeMixin, TenantScopedModel):
    """Findings & Corrective Actions (spec §31) — can originate from an
    audit, assessment, incident, risk review or management review,
    tracked via a generic link back to the source record."""

    REFERENCE_PREFIX = "CA"

    source = models.CharField(max_length=20, choices=SOURCE_CHOICES, default="other")
    content_type = models.ForeignKey(ContentType, on_delete=models.SET_NULL, null=True, blank=True)
    object_id = models.CharField(max_length=64, null=True, blank=True)
    source_record = GenericForeignKey("content_type", "object_id")

    finding_description = models.TextField()
    severity = models.CharField(max_length=20, choices=SEVERITY_CHOICES, default="medium")
    root_cause = models.TextField(blank=True)
    action_description = models.TextField(blank=True)
    owner = models.ForeignKey(
        settings.AUTH_USER_MODEL, on_delete=models.SET_NULL, null=True, blank=True, related_name="corrective_actions_owned"
    )
    due_date = models.DateField(null=True, blank=True)
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default=STATUS_OPEN)
    evidence = models.ManyToManyField("evidence.Evidence", blank=True, related_name="corrective_actions")
    verification_notes = models.TextField(blank=True)
    verified_by = models.ForeignKey(
        settings.AUTH_USER_MODEL, on_delete=models.SET_NULL, null=True, blank=True, related_name="+"
    )
    closed_at = models.DateTimeField(null=True, blank=True)

    class Meta:
        ordering = ["-created_at"]

    def __str__(self):
        return f"{self.reference_code} {self.finding_description[:60]}"

    def save(self, *args, **kwargs):
        self.assign_reference_code()
        super().save(*args, **kwargs)

    @property
    def is_overdue(self):
        from django.utils import timezone

        return bool(self.due_date and self.due_date < timezone.now().date() and self.status != STATUS_CLOSED)
