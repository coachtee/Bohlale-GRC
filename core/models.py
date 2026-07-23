import uuid

from django.db import models


class TimeStampedModel(models.Model):
    """Abstract base adding created/updated timestamps."""

    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        abstract = True


class TenantScopedModel(TimeStampedModel):
    """
    Abstract base for every model that belongs to exactly one
    organisation (tenant). This is the backbone of Bohlale GRC's
    row-level multi-tenancy: every query against a tenant-scoped model
    must be filtered by `organisation` (see core.mixins for the view
    helpers that enforce this).
    """

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    organisation = models.ForeignKey(
        "tenancy.Organisation",
        on_delete=models.CASCADE,
        related_name="%(app_label)s_%(class)s_set",
    )

    class Meta:
        abstract = True


class ReferenceCodeMixin(models.Model):
    """
    Abstract mixin for models that need a human-readable, per-organisation
    sequential reference code (e.g. RISK-0001, DOC-0003, INC-0012).
    Subclasses must set `REFERENCE_PREFIX` and call
    `self.assign_reference_code()` in `save()` before the first save.
    """

    REFERENCE_PREFIX = "REF"
    reference_code = models.CharField(max_length=32, blank=True, db_index=True)

    class Meta:
        abstract = True

    def assign_reference_code(self):
        if self.reference_code:
            return
        cls = self.__class__
        existing = cls.objects.filter(organisation=self.organisation).count()
        self.reference_code = f"{self.REFERENCE_PREFIX}-{existing + 1:04d}"
