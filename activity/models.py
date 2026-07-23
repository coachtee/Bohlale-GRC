import uuid

from django.conf import settings
from django.contrib.contenttypes.fields import GenericForeignKey
from django.contrib.contenttypes.models import ContentType
from django.db import models


class AuditLog(models.Model):
    """
    Immutable audit trail entry. Sensitive/state-changing actions across
    every module are recorded here (spec §6, §44, §45). Entries are
    never edited or deleted through the application.
    """

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    organisation = models.ForeignKey(
        "tenancy.Organisation",
        on_delete=models.CASCADE,
        related_name="audit_logs",
        null=True,
        blank=True,
        help_text="Null for platform-level events (e.g. organisation creation).",
    )
    actor = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="audit_actions",
    )
    action = models.CharField(max_length=64)
    description = models.CharField(max_length=500, blank=True)

    content_type = models.ForeignKey(
        ContentType, on_delete=models.SET_NULL, null=True, blank=True
    )
    object_id = models.CharField(max_length=64, null=True, blank=True)
    target = GenericForeignKey("content_type", "object_id")

    metadata = models.JSONField(default=dict, blank=True)
    ip_address = models.GenericIPAddressField(null=True, blank=True)
    created_at = models.DateTimeField(auto_now_add=True, db_index=True)

    class Meta:
        ordering = ["-created_at"]
        indexes = [
            models.Index(fields=["organisation", "-created_at"]),
        ]

    def __str__(self):
        who = self.actor.get_full_name() if self.actor else "System"
        return f"{who} {self.action} — {self.description or self.object_id}"
