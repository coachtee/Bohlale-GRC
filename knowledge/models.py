from django.conf import settings
from django.db import models

from core.models import TenantScopedModel

CATEGORY_CHOICES = [
    ("organisation_profile", "Organisation Profile"),
    ("business_activities", "Business Activities"),
    ("products_services", "Products & Services"),
    ("locations", "Locations"),
    ("departments", "Departments"),
    ("people_roles", "People & Roles"),
    ("processes", "Processes"),
    ("information", "Information"),
    ("personal_information", "Personal Information"),
    ("systems", "Systems"),
    ("applications", "Applications"),
    ("assets", "Assets"),
    ("suppliers", "Suppliers"),
    ("third_parties", "Third Parties"),
    ("interested_parties", "Interested Parties"),
    ("regulatory_requirements", "Regulatory Requirements"),
    ("contractual_requirements", "Contractual Requirements"),
    ("existing_policies", "Existing Policies"),
    ("risks", "Risks"),
    ("controls", "Controls"),
]

STATUS_VERIFIED = "verified"
STATUS_AI_INFERENCE = "ai_inference"
STATUS_MISSING = "missing"

STATUS_CHOICES = [
    (STATUS_VERIFIED, "Verified"),
    (STATUS_AI_INFERENCE, "AI Inference"),
    (STATUS_MISSING, "Missing"),
]


class KnowledgeItem(TenantScopedModel):
    """
    One fact in the Organisation Knowledge Profile (spec §10) — the
    contextual foundation the AI assistant draws on. Facts are always
    labelled by provenance (verified / AI inference / missing) so AI
    generation can prioritise verified organisational facts over its
    own prior suggestions.
    """

    category = models.CharField(max_length=40, choices=CATEGORY_CHOICES)
    label = models.CharField(max_length=200)
    value = models.TextField(blank=True)
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default=STATUS_MISSING)
    source = models.CharField(max_length=200, blank=True, help_text="e.g. Organisation Interview, Information Request, Manual Entry")
    verified_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="knowledge_items_verified",
    )
    verified_at = models.DateTimeField(null=True, blank=True)

    class Meta:
        ordering = ["category", "label"]
        constraints = [
            models.UniqueConstraint(
                fields=["organisation", "category", "label"], name="unique_knowledge_item_per_org"
            )
        ]

    def __str__(self):
        return f"{self.get_category_display()}: {self.label}"

    def mark_verified(self, user):
        from django.utils import timezone

        self.status = STATUS_VERIFIED
        self.verified_by = user
        self.verified_at = timezone.now()
        self.save(update_fields=["status", "verified_by", "verified_at", "updated_at"])
