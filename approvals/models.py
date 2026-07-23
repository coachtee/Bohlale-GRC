import uuid

from django.conf import settings
from django.contrib.contenttypes.fields import GenericForeignKey
from django.contrib.contenttypes.models import ContentType
from django.db import models

from core.models import TenantScopedModel

REQUEST_PENDING = "pending"
REQUEST_APPROVED = "approved"
REQUEST_REJECTED = "rejected"

REQUEST_STATUS_CHOICES = [
    (REQUEST_PENDING, "Pending"),
    (REQUEST_APPROVED, "Approved"),
    (REQUEST_REJECTED, "Rejected"),
]


class ApprovalRequest(TenantScopedModel):
    """A request for sign-off on a controlled record (currently:
    documents.Document). Generic so other record types (e.g. an audit
    report) can reuse the same approval/e-signature mechanism later."""

    content_type = models.ForeignKey(ContentType, on_delete=models.CASCADE)
    object_id = models.CharField(max_length=64)
    target = GenericForeignKey("content_type", "object_id")

    requested_by = models.ForeignKey(
        settings.AUTH_USER_MODEL, on_delete=models.SET_NULL, null=True, related_name="approval_requests_made"
    )
    status = models.CharField(max_length=20, choices=REQUEST_STATUS_CHOICES, default=REQUEST_PENDING)
    decided_at = models.DateTimeField(null=True, blank=True)

    class Meta:
        ordering = ["-created_at"]

    def __str__(self):
        return f"Approval request: {self.target} ({self.status})"


class Signature(models.Model):
    """
    An immutable electronic sign-off record (spec §16): approver
    identity + role, decision, typed signature + explicit consent,
    timestamp, IP address, and a snapshot of the exact document
    version/hash being approved — so the signature can always be tied
    back to precisely what was signed, even if the document changes
    again later.
    """

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    approval_request = models.ForeignKey(ApprovalRequest, on_delete=models.CASCADE, related_name="signatures")
    approver = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.SET_NULL, null=True)
    role = models.CharField(max_length=100, blank=True)
    decision = models.CharField(max_length=20, choices=[("approved", "Approved"), ("rejected", "Rejected")])
    typed_signature = models.CharField(max_length=200)
    consent = models.BooleanField(default=False)
    document_version = models.CharField(max_length=20, blank=True)
    document_hash = models.CharField(max_length=64, blank=True)
    ip_address = models.GenericIPAddressField(null=True, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ["-created_at"]

    def __str__(self):
        return f"{self.typed_signature} — {self.decision} ({self.created_at:%Y-%m-%d})"
