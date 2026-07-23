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

    def save(self, *args, **kwargs):
        """
        Wraps assignment + the actual INSERT/UPDATE in one atomic
        transaction so the Organisation row-lock taken in
        `assign_reference_code()` is held through to the write that
        makes the new count visible to the next caller — see that
        method's docstring. Subclasses with extra `save()` logic of
        their own (e.g. computing a derived field) should do that
        first, then call `super().save(*args, **kwargs)` to reach this.
        """
        from django.db import transaction

        with transaction.atomic():
            self.assign_reference_code()
            super().save(*args, **kwargs)

    def assign_reference_code(self):
        """
        Assigns the next sequential code for this model within the
        organisation. Locks the owning Organisation row for the
        duration (`select_for_update`) so two concurrent requests
        creating a record for the same organisation (realistic under
        multiple Gunicorn workers) can't both read the same count and
        assign the same reference code — the second request blocks
        until the first commits, then sees the incremented count. A
        no-op on SQLite (which doesn't implement row-level locking) but
        effective on PostgreSQL, the documented production database.
        Must be called from within the transaction.atomic() block that
        also performs the save — see `save()` above.
        """
        if self.reference_code:
            return
        from tenancy.models import Organisation

        cls = self.__class__
        Organisation.objects.select_for_update().filter(pk=self.organisation_id).first()
        existing = cls.objects.filter(organisation_id=self.organisation_id).count()
        self.reference_code = f"{self.REFERENCE_PREFIX}-{existing + 1:04d}"
