import uuid

from django.conf import settings
from django.db import models


class Notification(models.Model):
    CATEGORY_CHOICES = [
        ("action_overdue", "Overdue Action"),
        ("document_review", "Document Review"),
        ("risk_review", "Risk Review"),
        ("evidence_expiry", "Evidence Expiry"),
        ("audit", "Audit"),
        ("approval", "Approval"),
        ("information_request", "Assigned Question"),
        ("incident", "Incident"),
        ("general", "General"),
    ]

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    organisation = models.ForeignKey(
        "tenancy.Organisation", on_delete=models.CASCADE, related_name="notifications"
    )
    recipient = models.ForeignKey(
        settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name="notifications"
    )
    category = models.CharField(max_length=30, choices=CATEGORY_CHOICES, default="general")
    message = models.CharField(max_length=300)
    link = models.CharField(max_length=300, blank=True)
    is_read = models.BooleanField(default=False)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ["-created_at"]

    def __str__(self):
        return self.message
