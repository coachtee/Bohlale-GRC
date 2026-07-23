from django.conf import settings
from django.db import models

from core.models import ReferenceCodeMixin, TenantScopedModel

CATEGORY_CHOICES = [
    ("information_security", "Information Security"),
    ("operational", "Operational"),
    ("financial", "Financial"),
    ("compliance", "Compliance / Regulatory"),
    ("strategic", "Strategic"),
    ("reputational", "Reputational"),
    ("third_party", "Third Party / Supplier"),
    ("people", "People"),
    ("other", "Other"),
]

TREATMENT_CHOICES = [
    ("avoid", "Avoid"),
    ("mitigate", "Mitigate"),
    ("transfer", "Transfer"),
    ("accept", "Accept"),
]

STATUS_OPEN = "open"
STATUS_IN_TREATMENT = "in_treatment"
STATUS_ACCEPTED = "accepted"
STATUS_CLOSED = "closed"

STATUS_CHOICES = [
    (STATUS_OPEN, "Open"),
    (STATUS_IN_TREATMENT, "In Treatment"),
    (STATUS_ACCEPTED, "Accepted"),
    (STATUS_CLOSED, "Closed"),
]

RATING_SCALE = [(i, str(i)) for i in range(1, 6)]


class RiskMatrixConfig(TenantScopedModel):
    """
    Configurable risk methodology (spec §21): a simple 1-5 x 1-5
    likelihood/impact matrix whose score bands (out of 25) are
    adjustable per organisation. Defaults match a conventional
    4-band (Very Low/Low/Medium/High) scheme.
    """

    very_low_max = models.PositiveSmallIntegerField(default=4)
    low_max = models.PositiveSmallIntegerField(default=9)
    medium_max = models.PositiveSmallIntegerField(default=15)

    class Meta:
        constraints = [
            models.UniqueConstraint(fields=["organisation"], name="unique_risk_matrix_per_org")
        ]

    def save(self, *args, **kwargs):
        from django.core.cache import cache

        super().save(*args, **kwargs)
        cache.delete(f"risk_matrix:{self.organisation_id}")

    def band_for_score(self, score):
        if score <= self.very_low_max:
            return "very_low", "Very Low"
        if score <= self.low_max:
            return "low", "Low"
        if score <= self.medium_max:
            return "medium", "Medium"
        return "high", "High"


class Risk(ReferenceCodeMixin, TenantScopedModel):
    REFERENCE_PREFIX = "RISK"

    title = models.CharField(max_length=250)
    description = models.TextField(blank=True)
    category = models.CharField(max_length=30, choices=CATEGORY_CHOICES, default="information_security")
    asset_process = models.CharField(max_length=250, blank=True, help_text="Affected asset or business process")
    threat = models.CharField(max_length=300, blank=True)
    vulnerability = models.CharField(max_length=300, blank=True)

    likelihood = models.PositiveSmallIntegerField(choices=RATING_SCALE, default=3)
    impact = models.PositiveSmallIntegerField(choices=RATING_SCALE, default=3)
    inherent_risk_score = models.PositiveSmallIntegerField(default=9, editable=False)

    existing_controls = models.TextField(blank=True)

    residual_likelihood = models.PositiveSmallIntegerField(choices=RATING_SCALE, null=True, blank=True)
    residual_impact = models.PositiveSmallIntegerField(choices=RATING_SCALE, null=True, blank=True)
    residual_risk_score = models.PositiveSmallIntegerField(null=True, blank=True, editable=False)

    owner = models.ForeignKey(
        settings.AUTH_USER_MODEL, on_delete=models.SET_NULL, null=True, blank=True, related_name="risks_owned"
    )
    treatment = models.CharField(max_length=20, choices=TREATMENT_CHOICES, default="mitigate")
    treatment_owner = models.ForeignKey(
        settings.AUTH_USER_MODEL, on_delete=models.SET_NULL, null=True, blank=True, related_name="risk_treatments_owned"
    )
    treatment_plan = models.TextField(blank=True)
    due_date = models.DateField(null=True, blank=True)
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default=STATUS_OPEN)

    related_requirements = models.ManyToManyField("frameworks.Requirement", blank=True, related_name="risks")

    class Meta:
        ordering = ["-inherent_risk_score"]

    def __str__(self):
        return f"{self.reference_code} {self.title}"

    def save(self, *args, **kwargs):
        self.inherent_risk_score = self.likelihood * self.impact
        if self.residual_likelihood and self.residual_impact:
            self.residual_risk_score = self.residual_likelihood * self.residual_impact
        else:
            self.residual_risk_score = None
        super().save(*args, **kwargs)

    def get_matrix(self):
        """
        Cached for a short TTL: `inherent_band`/`residual_band` call
        this once per risk, and without caching, rendering a 50-row
        risk register would issue up to 50 extra `get_or_create` queries
        for what is, within one organisation, always the same matrix.
        Invalidated immediately on RiskMatrixConfig.save(), so admin
        changes to the matrix take effect right away rather than after
        the TTL — the TTL only covers the (much more common) unchanged
        case.
        """
        from django.core.cache import cache

        cache_key = f"risk_matrix:{self.organisation_id}"
        matrix = cache.get(cache_key)
        if matrix is None:
            matrix, _ = RiskMatrixConfig.objects.get_or_create(organisation=self.organisation)
            cache.set(cache_key, matrix, 60)
        return matrix

    @property
    def inherent_band(self):
        return self.get_matrix().band_for_score(self.inherent_risk_score)

    @property
    def residual_band(self):
        if self.residual_risk_score is None:
            return None
        return self.get_matrix().band_for_score(self.residual_risk_score)
