import uuid

from django.conf import settings
from django.contrib.contenttypes.fields import GenericForeignKey
from django.contrib.contenttypes.models import ContentType
from django.db import models

STATUS_PENDING = "pending_review"
STATUS_APPROVED = "approved"
STATUS_REJECTED = "rejected"
STATUS_EDITED = "edited"

REVIEW_STATUS_CHOICES = [
    (STATUS_PENDING, "Pending Human Review"),
    (STATUS_APPROVED, "Approved As-Is"),
    (STATUS_EDITED, "Edited Then Approved"),
    (STATUS_REJECTED, "Rejected"),
]


class AIGeneration(models.Model):
    """
    Immutable AI governance record (spec §38): every AI-generated
    output must be traceable to provider, model, purpose, the user who
    requested it, what context was used, and — once a human has acted
    on it — who reviewed it and what they decided. AI-generated content
    can never become an approved/published record without a
    corresponding AIGeneration whose review_status is 'approved' or
    'edited'.
    """

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    organisation = models.ForeignKey(
        "tenancy.Organisation", on_delete=models.CASCADE, related_name="ai_generations"
    )
    requested_by = models.ForeignKey(
        settings.AUTH_USER_MODEL, on_delete=models.SET_NULL, null=True, related_name="ai_generations"
    )
    purpose = models.CharField(max_length=60)
    provider = models.CharField(max_length=40)
    model = models.CharField(max_length=100)
    context_reference = models.TextField(
        blank=True, help_text="Human-readable summary of what context/knowledge was used."
    )
    output_text = models.TextField()
    output_version = models.PositiveIntegerField(default=1)

    content_type = models.ForeignKey(ContentType, on_delete=models.SET_NULL, null=True, blank=True)
    object_id = models.CharField(max_length=64, null=True, blank=True)
    related_object = GenericForeignKey("content_type", "object_id")

    review_status = models.CharField(max_length=20, choices=REVIEW_STATUS_CHOICES, default=STATUS_PENDING)
    reviewed_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="ai_generations_reviewed",
    )
    reviewed_at = models.DateTimeField(null=True, blank=True)

    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ["-created_at"]

    def __str__(self):
        return f"{self.purpose} ({self.provider}/{self.model}) — {self.review_status}"

    def mark_reviewed(self, user, status):
        from django.utils import timezone

        self.review_status = status
        self.reviewed_by = user
        self.reviewed_at = timezone.now()
        self.save(update_fields=["review_status", "reviewed_by", "reviewed_at"])
