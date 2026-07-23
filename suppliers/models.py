from django.conf import settings
from django.db import models

from core.models import ReferenceCodeMixin, TenantScopedModel

CRITICALITY_CHOICES = [
    ("low", "Low"),
    ("medium", "Medium"),
    ("high", "High"),
    ("critical", "Critical"),
]

RISK_RATING_CHOICES = [
    ("low", "Low"),
    ("medium", "Medium"),
    ("high", "High"),
]

STATUS_CHOICES = [
    ("active", "Active"),
    ("under_review", "Under Review"),
    ("terminated", "Terminated"),
]


class Supplier(ReferenceCodeMixin, TenantScopedModel):
    REFERENCE_PREFIX = "SUP"

    name = models.CharField(max_length=200)
    service = models.CharField(max_length=300, blank=True)
    owner = models.ForeignKey(
        settings.AUTH_USER_MODEL, on_delete=models.SET_NULL, null=True, blank=True, related_name="suppliers_owned"
    )
    criticality = models.CharField(max_length=20, choices=CRITICALITY_CHOICES, default="medium")
    data_access = models.BooleanField(default=False)
    personal_info_access = models.BooleanField(default=False)
    risk_rating = models.CharField(max_length=20, choices=RISK_RATING_CHOICES, default="medium")
    assessment_notes = models.TextField(blank=True)
    contract_review_date = models.DateField(null=True, blank=True)
    review_date = models.DateField(null=True, blank=True)
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default="active")

    class Meta:
        ordering = ["name"]

    def __str__(self):
        return f"{self.reference_code} {self.name}"

    def save(self, *args, **kwargs):
        self.assign_reference_code()
        super().save(*args, **kwargs)

    @property
    def is_review_overdue(self):
        from django.utils import timezone

        return bool(self.review_date and self.review_date < timezone.now().date())
