import hashlib
import uuid

from django.conf import settings
from django.db import models

from core.models import ReferenceCodeMixin, TenantScopedModel
from core.validators import validate_upload_file

DOC_TYPE_CHOICES = [
    ("isms_scope", "ISMS Scope"),
    ("information_security_policy", "Information Security Policy"),
    ("risk_management_procedure", "Risk Management Procedure"),
    ("access_control_policy", "Access Control Policy"),
    ("incident_management_procedure", "Incident Management Procedure"),
    ("supplier_security_policy", "Supplier Security Policy"),
    ("popia_policy", "POPIA / Data Protection Policy"),
    ("policy", "Policy"),
    ("procedure", "Procedure"),
    ("register", "Register Document"),
    ("form", "Form / Template"),
    ("other", "Other"),
]

CLASSIFICATION_CHOICES = [
    ("public", "Public"),
    ("internal", "Internal"),
    ("confidential", "Confidential"),
    ("restricted", "Restricted"),
]

STATUS_DRAFT = "draft"
STATUS_UNDER_REVIEW = "under_review"
STATUS_AWAITING_APPROVAL = "awaiting_approval"
STATUS_APPROVED = "approved"
STATUS_PUBLISHED = "published"
STATUS_SUPERSEDED = "superseded"
STATUS_ARCHIVED = "archived"

STATUS_CHOICES = [
    (STATUS_DRAFT, "Draft"),
    (STATUS_UNDER_REVIEW, "Under Review"),
    (STATUS_AWAITING_APPROVAL, "Awaiting Approval"),
    (STATUS_APPROVED, "Approved"),
    (STATUS_PUBLISHED, "Published"),
    (STATUS_SUPERSEDED, "Superseded"),
    (STATUS_ARCHIVED, "Archived"),
]


def document_upload_path(instance, filename):
    return f"documents/{instance.organisation_id}/{filename}"


class Document(ReferenceCodeMixin, TenantScopedModel):
    """A controlled document (spec §14). `content` holds the current
    text; published history lives in DocumentVersion snapshots."""

    REFERENCE_PREFIX = "DOC"

    title = models.CharField(max_length=250)
    doc_type = models.CharField(max_length=40, choices=DOC_TYPE_CHOICES, default="policy")
    version_label = models.CharField(max_length=20, default="0.1")
    content = models.TextField(blank=True)

    owner = models.ForeignKey(
        settings.AUTH_USER_MODEL, on_delete=models.SET_NULL, null=True, blank=True, related_name="documents_owned"
    )
    author = models.ForeignKey(
        settings.AUTH_USER_MODEL, on_delete=models.SET_NULL, null=True, blank=True, related_name="documents_authored"
    )
    approver = models.ForeignKey(
        settings.AUTH_USER_MODEL, on_delete=models.SET_NULL, null=True, blank=True, related_name="documents_approved"
    )
    approval_date = models.DateField(null=True, blank=True)
    effective_date = models.DateField(null=True, blank=True)
    next_review_date = models.DateField(null=True, blank=True)
    classification = models.CharField(max_length=20, choices=CLASSIFICATION_CHOICES, default="internal")
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default=STATUS_DRAFT)

    related_frameworks = models.ManyToManyField("frameworks.Framework", blank=True, related_name="documents")
    related_requirements = models.ManyToManyField("frameworks.Requirement", blank=True, related_name="documents")

    attachment = models.FileField(
        upload_to=document_upload_path, blank=True, null=True, validators=[validate_upload_file]
    )

    ai_generated = models.BooleanField(default=False)
    ai_generation = models.ForeignKey(
        "ai.AIGeneration", on_delete=models.SET_NULL, null=True, blank=True, related_name="documents"
    )
    journey_step = models.ForeignKey(
        "journeys.JourneyStep", on_delete=models.SET_NULL, null=True, blank=True, related_name="documents"
    )

    class Meta:
        ordering = ["-updated_at"]

    def __str__(self):
        return f"{self.reference_code} {self.title}"

    def content_hash(self):
        return hashlib.sha256(self.content.encode("utf-8")).hexdigest()

    def snapshot_version(self, user, change_reason=""):
        DocumentVersion.objects.create(
            document=self,
            version_label=self.version_label,
            content=self.content,
            status_at_snapshot=self.status,
            changed_by=user,
            change_reason=change_reason,
            document_hash=self.content_hash(),
        )

    @property
    def is_review_overdue(self):
        from django.utils import timezone

        return bool(self.next_review_date and self.next_review_date < timezone.now().date())

    @property
    def is_review_due_soon(self):
        from datetime import timedelta

        from django.utils import timezone

        if not self.next_review_date:
            return False
        today = timezone.now().date()
        return today <= self.next_review_date <= today + timedelta(days=30)


class DocumentVersion(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    document = models.ForeignKey(Document, on_delete=models.CASCADE, related_name="versions")
    version_label = models.CharField(max_length=20)
    content = models.TextField(blank=True)
    status_at_snapshot = models.CharField(max_length=20, choices=STATUS_CHOICES, blank=True)
    changed_by = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.SET_NULL, null=True)
    change_reason = models.CharField(max_length=300, blank=True)
    document_hash = models.CharField(max_length=64, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ["-created_at"]

    def __str__(self):
        return f"{self.document.title} v{self.version_label}"
