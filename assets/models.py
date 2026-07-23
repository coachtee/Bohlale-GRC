from django.conf import settings
from django.db import models

from core.models import ReferenceCodeMixin, TenantScopedModel

ASSET_TYPE_CHOICES = [
    ("information", "Information Asset"),
    ("system", "System"),
    ("application", "Application"),
    ("hardware", "Hardware"),
    ("data_repository", "Data Repository"),
]

CLASSIFICATION_CHOICES = [
    ("public", "Public"),
    ("internal", "Internal"),
    ("confidential", "Confidential"),
    ("restricted", "Restricted"),
]

STATUS_CHOICES = [
    ("active", "Active"),
    ("planned", "Planned"),
    ("retired", "Retired"),
]


class Asset(ReferenceCodeMixin, TenantScopedModel):
    REFERENCE_PREFIX = "AST"

    name = models.CharField(max_length=200)
    asset_type = models.CharField(max_length=20, choices=ASSET_TYPE_CHOICES, default="information")
    owner = models.ForeignKey(
        settings.AUTH_USER_MODEL, on_delete=models.SET_NULL, null=True, blank=True, related_name="assets_owned"
    )
    classification = models.CharField(max_length=20, choices=CLASSIFICATION_CHOICES, default="internal")
    location = models.CharField(max_length=200, blank=True)
    description = models.TextField(blank=True)
    related_process = models.CharField(max_length=200, blank=True)
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default="active")

    related_risks = models.ManyToManyField("risks.Risk", blank=True, related_name="assets")
    related_controls = models.ManyToManyField("controls.Control", blank=True, related_name="assets")
    related_suppliers = models.ManyToManyField("suppliers.Supplier", blank=True, related_name="assets")

    class Meta:
        ordering = ["name"]

    def __str__(self):
        return f"{self.reference_code} {self.name}"

    def save(self, *args, **kwargs):
        self.assign_reference_code()
        super().save(*args, **kwargs)
