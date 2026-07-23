from django.conf import settings
from django.db import models

from core.models import ReferenceCodeMixin, TenantScopedModel
from core.validators import validate_upload_file

STATUS_CHOICES = [
    ("draft", "Draft"),
    ("completed", "Completed"),
]

# Original, plain-language summary of the kinds of input a management
# review should typically cover for a management system (not copied
# from any standard's mandated wording) — spec §32: "guide the
# organisation through required management-review inputs".
REQUIRED_INPUTS = [
    "Status of actions from previous management reviews",
    "Changes in external and internal issues relevant to the management system",
    "Performance information: nonconformities and corrective actions, monitoring/measurement results, "
    "audit results, and achievement of objectives",
    "Feedback from interested parties",
    "Results of risk assessment and status of the risk treatment plan",
    "Opportunities for continual improvement",
]


def review_attachment_path(instance, filename):
    return f"management_reviews/{instance.organisation_id}/{filename}"


class ManagementReview(ReferenceCodeMixin, TenantScopedModel):
    REFERENCE_PREFIX = "MR"

    framework = models.ForeignKey(
        "frameworks.Framework", on_delete=models.SET_NULL, null=True, blank=True, related_name="management_reviews"
    )
    meeting_date = models.DateField()
    attendees = models.TextField(blank=True, help_text="Names and roles of attendees.")
    agenda = models.TextField(blank=True)
    decisions = models.TextField(blank=True)
    approved_by = models.ForeignKey(
        settings.AUTH_USER_MODEL, on_delete=models.SET_NULL, null=True, blank=True, related_name="management_reviews_approved"
    )
    attachment = models.FileField(
        upload_to=review_attachment_path, blank=True, null=True, validators=[validate_upload_file]
    )
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default="draft")

    class Meta:
        ordering = ["-meeting_date"]

    def __str__(self):
        return f"{self.reference_code} — {self.meeting_date}"

    def save(self, *args, **kwargs):
        self.assign_reference_code()
        super().save(*args, **kwargs)

    @property
    def inputs_covered_count(self):
        return self.input_records.filter(covered=True).count()


class ManagementReviewInputRecord(models.Model):
    review = models.ForeignKey(ManagementReview, on_delete=models.CASCADE, related_name="input_records")
    label = models.CharField(max_length=300)
    covered = models.BooleanField(default=False)
    notes = models.TextField(blank=True)

    def __str__(self):
        return self.label
