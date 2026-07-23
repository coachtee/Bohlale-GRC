from django.conf import settings
from django.db import models

from core.models import ReferenceCodeMixin, TenantScopedModel
from core.validators import validate_upload_file

EVIDENCE_TYPE_CHOICES = [
    ("document", "Document"),
    ("screenshot", "Screenshot"),
    ("log_export", "Log Export"),
    ("record", "Record"),
    ("sign_off", "Sign-off / Approval Record"),
    ("other", "Other"),
]

VERIFICATION_STATUS_CHOICES = [
    ("unverified", "Unverified"),
    ("verified", "Verified"),
    ("rejected", "Rejected"),
]


def evidence_upload_path(instance, filename):
    return f"evidence/{instance.organisation_id}/{filename}"


class Evidence(ReferenceCodeMixin, TenantScopedModel):
    """Evidence attachable to controls, requirements, risks, audits and
    corrective actions (spec §23)."""

    REFERENCE_PREFIX = "EVD"

    name = models.CharField(max_length=250)
    evidence_type = models.CharField(max_length=20, choices=EVIDENCE_TYPE_CHOICES, default="document")
    owner = models.ForeignKey(
        settings.AUTH_USER_MODEL, on_delete=models.SET_NULL, null=True, blank=True, related_name="evidence_owned"
    )
    uploaded_by = models.ForeignKey(
        settings.AUTH_USER_MODEL, on_delete=models.SET_NULL, null=True, blank=True, related_name="evidence_uploaded"
    )
    file = models.FileField(upload_to=evidence_upload_path, blank=True, null=True, validators=[validate_upload_file])
    notes = models.TextField(blank=True)

    validity_period_months = models.PositiveSmallIntegerField(null=True, blank=True)
    expiry_date = models.DateField(null=True, blank=True)
    verification_status = models.CharField(max_length=20, choices=VERIFICATION_STATUS_CHOICES, default="unverified")

    related_controls = models.ManyToManyField("controls.Control", blank=True, related_name="evidence_items")
    related_requirements = models.ManyToManyField("frameworks.Requirement", blank=True, related_name="evidence_items")
    related_risks = models.ManyToManyField("risks.Risk", blank=True, related_name="evidence_items")

    class Meta:
        ordering = ["-created_at"]
        verbose_name_plural = "Evidence"

    def __str__(self):
        return f"{self.reference_code} {self.name}"

    def save(self, *args, **kwargs):
        self.assign_reference_code()
        super().save(*args, **kwargs)

    @property
    def is_expired(self):
        from django.utils import timezone

        return bool(self.expiry_date and self.expiry_date < timezone.now().date())

    @property
    def is_expiring_soon(self):
        from datetime import timedelta

        from django.utils import timezone

        if not self.expiry_date:
            return False
        today = timezone.now().date()
        return today <= self.expiry_date <= today + timedelta(days=30)
